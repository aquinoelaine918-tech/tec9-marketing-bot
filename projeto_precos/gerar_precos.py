import os
import pandas as pd
from pathlib import Path
import smtplib
from email.message import EmailMessage

# =========================
# CONFIGURAÇÕES
# =========================
ARQUIVO_ENTRADA = os.getenv("ARQUIVO_ENTRADA", "produtos_atualizados.xlsx")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "."))
ARQUIVO_SAIDA = OUTPUT_DIR / os.getenv("ARQUIVO_SAIDA", "precificacao_automatica.xlsx")

MARGEM_MINIMA = float(os.getenv("MARGEM_MINIMA_SEGURANCA", 15))
TOLERANCIA = float(os.getenv("TOLERANCIA_COMPETITIVA", 3))
AJUSTE_URGENTE = float(os.getenv("AJUSTE_URGENTE", 8))
ALVO = float(os.getenv("ALVO_COMPETITIVO", 1.5))

EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")

# =========================
# GARANTIR PASTA
# =========================
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# LEITURA E PADRONIZAÇÃO
# =========================
try:
    df = pd.read_excel(ARQUIVO_ENTRADA)
    
    # Limpa espaços e coloca tudo em MAIÚSCULO
    df.columns = df.columns.str.strip().str.upper()

    # LOG DE SEGURANÇA: Mostra o que o script achou no Excel
    print(f"--- Colunas detectadas no arquivo: {df.columns.tolist()}")

    # MAPEAMENTO FLEXÍVEL (Se a coluna tiver outro nome, ele corrige aqui)
    mapeamento = {
        'CUSTO': 'CUSTO_TRATADO',
        'VALOR_CUSTO': 'CUSTO_TRATADO',
        'PRECO': 'PRECO_VENDA',
        'VALOR_VENDA': 'PRECO_VENDA',
        'MARGEM': 'MARGEM_%'
    }
    df.rename(columns=mapeamento, inplace=True)

except Exception as e:
    print(f"Erro ao ler o arquivo {ARQUIVO_ENTRADA}: {e}")
    exit(1)

# =========================
# GARANTIR COLUNAS
# =========================
if "PRODUTO" not in df.columns:
    df["PRODUTO"] = ""

colunas_necessarias = ["SKU", "CUSTO_TRATADO", "PRECO_VENDA", "MARGEM_%"]
for coluna in colunas_necessarias:
    if coluna not in df.columns:
        # Erro detalhado para você saber qual coluna faltou no Excel
        raise Exception(f"ERRO: A coluna '{coluna}' não existe no Excel. Verifique o arquivo!")

# =========================
# CALCULOS (Com tratamento para evitar erro de tipo)
# =========================
df["CUSTO_TRATADO"] = pd.to_numeric(df["CUSTO_TRATADO"], errors='coerce')
df["PRECO_VENDA"] = pd.to_numeric(df["PRECO_VENDA"], errors='coerce')

df["PRECO_SUGERIDO"] = df["CUSTO_TRATADO"] * (1 + MARGEM_MINIMA / 100)
df["DIFERENCA_R$"] = df["PRECO_VENDA"] - df["PRECO_SUGERIDO"]
df["DIFERENCA_%"] = (df["DIFERENCA_R$"] / df["PRECO_SUGERIDO"]) * 100

# =========================
# CLASSIFICAÇÃO
# =========================
def classificar(row):
    if pd.isna(row["DIFERENCA_%"]): return "ERRO_DADOS"
    if row["DIFERENCA_%"] < -AJUSTE_URGENTE:
        return "AJUSTE URGENTE"
    elif row["DIFERENCA_%"] < -TOLERANCIA:
        return "ABAIXO DO MERCADO"
    elif row["DIFERENCA_%"] > TOLERANCIA:
        return "ACIMA DO MERCADO"
    else:
        return "COMPETITIVO"

df["STATUS"] = df.apply(classificar, axis=1)

# =========================
# AÇÃO AUTOMÁTICA
# =========================
def acao(row):
    if row["STATUS"] == "AJUSTE URGENTE":
        return "SUBIR PREÇO URGENTE"
    elif row["STATUS"] == "ABAIXO DO MERCADO":
        return "SUBIR PREÇO"
    elif row["STATUS"] == "ACIMA DO MERCADO":
        return "REDUZIR PREÇO"
    else:
        return "MANTER"

df["ACAO"] = df.apply(acao, axis=1)

# =========================
# RESUMO BI
# =========================
resumo = df["STATUS"].value_counts()

total = len(df)
competitivo = int(resumo.get("COMPETITIVO", 0))
acima = int(resumo.get("ACIMA DO MERCADO", 0))
abaixo = int(resumo.get("ABAIXO DO MERCADO", 0))
urgente = int(resumo.get("AJUSTE URGENTE", 0))

# =========================
# ORGANIZAR COLUNAS
# =========================
colunas_finais = [
    "SKU",
    "PRODUTO",
    "CUSTO_TRATADO",
    "PRECO_VENDA",
    "MARGEM_%",
    "PRECO_SUGERIDO",
    "DIFERENCA_R$",
    "DIFERENCA_%",
    "STATUS",
    "ACAO",
]
df = df[colunas_finais]

# =========================
# SALVAR EXCEL
# =========================
with pd.ExcelWriter(ARQUIVO_SAIDA, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Analise", index=False)
    resumo.to_frame("Quantidade").to_excel(writer, sheet_name="Resumo")

# =========================
# PRINT LOG
# =========================
print("\n📊 RESUMO:")
print(f"TOTAL: {total}")
print(f"COMPETITIVO: {competitivo}")
print(f"ACIMA: {acima}")
print(f"ABAIXO: {abaixo}")
print(f"URGENTE: {urgente}")

print("\n✅ Arquivo gerado:", ARQUIVO_SAIDA)

# =========================
# ENVIO EMAIL
# =========================
if EMAIL_ENABLED:
    try:
        msg = EmailMessage()
        msg["Subject"] = "Relatório Automático TEC9"
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        corpo = f"""
RELATÓRIO AUTOMÁTICO TEC9

Total de produtos: {total}

Competitivos: {competitivo}
Acima do mercado: {acima}
Abaixo do mercado: {abaixo}
Ajuste urgente: {urgente}
"""
        msg.set_content(corpo)

        with open(ARQUIVO_SAIDA, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="octet-stream",
                filename=ARQUIVO_SAIDA.name
            )

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print("📧 Email enviado com sucesso!")

    except Exception as e:
        print("Erro ao enviar email:", e)
