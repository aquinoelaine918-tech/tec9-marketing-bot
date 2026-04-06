import pandas as pd
import requests
import time
import os
from datetime import datetime, timedelta

# ================= CONFIGURAÇÕES =================

API_KEY = (os.getenv("BREVO_API_KEY") or "").strip()
REMETENTE_EMAIL = (os.getenv("REMETENTE_EMAIL") or "").strip()
REMETENTE_NOME = "TEC9 Informática"
EMAIL_RELATORIO = (os.getenv("EMAIL_RELATORIO") or "comercial@tec9informatica.com.br").strip()

# O código tenta encontrar automaticamente um destes arquivos
ARQUIVOS_CLIENTES_POSSIVEIS = [
    "Clientes_TEC9.xlsx.csv",
    "Clientes_TEC9.csv",
    "Clientes_TEC9.xlsx",
]

ARQUIVO_HISTORICO = "historico_envios.csv"

# Limite de teste agora
LIMITE_DIARIO = 5000

# URL CORRETA DA API BREVO
URL_ENVIO_BREVO = "https://api.brevo.com/v3/smtp/email"

# ================= CAMPANHAS =================

CAMPANHAS = [
    {
        "nome": "SEMANA_1",
        "assunto": "Sua empresa pode estar gastando mais do que deveria com TI",
        "html": """
        <p>Olá, tudo bem?</p>
        <p>Podemos ajudar sua empresa a reduzir custos com tecnologia e melhorar o desempenho do seu ambiente de TI.</p>
        <p><b>TEC9 Informática</b><br>
        Soluções em computadores, periféricos, upgrades e equipamentos corporativos.</p>
        <p>Responda este e-mail ou fale com a nossa equipe.</p>
        """
    }
]

# ================= FUNÇÕES =================

def validar_configuracoes():
    if not API_KEY:
        raise ValueError("BREVO_API_KEY não configurada.")
    if not REMETENTE_EMAIL:
        raise ValueError("REMETENTE_EMAIL não configurada.")

def obter_campanha():
    semana = datetime.now().isocalendar()[1]
    return CAMPANHAS[semana % len(CAMPANHAS)]

def encontrar_arquivo_clientes():
    for arquivo in ARQUIVOS_CLIENTES_POSSIVEIS:
        if os.path.exists(arquivo):
            return arquivo
    raise FileNotFoundError(
        "Nenhum arquivo de clientes encontrado. "
        f"Arquivos procurados: {', '.join(ARQUIVOS_CLIENTES_POSSIVEIS)}"
    )

def carregar_clientes():
    arquivo = encontrar_arquivo_clientes()
    print(f"📂 Arquivo de clientes encontrado: {arquivo}")

    if arquivo.lower().endswith(".xlsx"):
        df = pd.read_excel(arquivo)
    else:
        df = pd.read_csv(arquivo)

    df.columns = [str(c).lower().strip() for c in df.columns]

    if "email" not in df.columns:
        raise ValueError("A planilha precisa ter uma coluna chamada 'email'.")

    df["email"] = df["email"].astype(str).str.strip().str.lower()
    df = df[df["email"].notna()]
    df = df[df["email"] != ""]
    df = df.drop_duplicates(subset=["email"])

    print(f"📋 Total de contatos válidos encontrados: {len(df)}")
    return df

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        print("📁 Histórico não encontrado. Será criado no primeiro envio.")
        return pd.DataFrame(columns=["email", "data", "campanha"])

    df = pd.read_csv(ARQUIVO_HISTORICO)
    if "email" not in df.columns:
        return pd.DataFrame(columns=["email", "data", "campanha"])

    df["email"] = df["email"].astype(str).str.strip().str.lower()
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    return df

def filtrar_clientes(df_clientes, df_historico):
    hoje = datetime.now()
    limite = hoje - timedelta(days=7)

    enviados_recentes = df_historico[df_historico["data"] >= limite]["email"].dropna().unique()
    df_filtrado = df_clientes[~df_clientes["email"].isin(enviados_recentes)]

    print(f"📨 Contatos elegíveis para envio agora: {len(df_filtrado)}")
    return df_filtrado.head(LIMITE_DIARIO)

def enviar_email(email, campanha):
    headers = {
        "accept": "application/json",
        "api-key": API_KEY,
        "content-type": "application/json"
    }

    payload = {
        "sender": {
            "name": REMETENTE_NOME,
            "email": REMETENTE_EMAIL
        },
        "to": [
            {"email": email}
        ],
        "subject": campanha["assunto"],
        "htmlContent": campanha["html"]
    }

    try:
        response = requests.post(URL_ENVIO_BREVO, json=payload, headers=headers, timeout=30)
        return response.status_code, response.text
    except Exception as e:
        return None, str(e)

def salvar_historico(registros):
    df_novo = pd.DataFrame(registros)

    if os.path.exists(ARQUIVO_HISTORICO):
        df_antigo = pd.read_csv(ARQUIVO_HISTORICO)
        df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
    else:
        df_final = df_novo

    df_final.to_csv(ARQUIVO_HISTORICO, index=False)
    print(f"💾 Histórico salvo em: {ARQUIVO_HISTORICO}")

def enviar_relatorio(enviados, campanha_nome):
    headers = {
        "accept": "application/json",
        "api-key": API_KEY,
        "content-type": "application/json"
    }

    html = f"""
    <h2>📊 Relatório TEC9</h2>
    <p><b>Campanha:</b> {campanha_nome}</p>
    <p><b>E-mails enviados com sucesso:</b> {enviados}</p>
    <p><b>Data/Hora:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    """

    payload = {
        "sender": {
            "name": REMETENTE_NOME,
            "email": REMETENTE_EMAIL
        },
        "to": [
            {"email": EMAIL_RELATORIO}
        ],
        "subject": f"Relatório diário TEC9 - {campanha_nome}",
        "htmlContent": html
    }

    try:
        response = requests.post(URL_ENVIO_BREVO, json=payload, headers=headers, timeout=30)
        print(f"📨 Relatório enviado para {EMAIL_RELATORIO} - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao enviar relatório: {e}")

# ================= EXECUÇÃO =================

def main():
    print("🚀 INICIANDO DISPARO AUTOMÁTICO TEC9")

    try:
        validar_configuracoes()

        campanha = obter_campanha()
        print(f"📢 Campanha atual: {campanha['nome']}")

        clientes = carregar_clientes()
        historico = carregar_historico()
        lista_envio = filtrar_clientes(clientes, historico)

        print(f"📧 Total de envios programados para agora: {len(lista_envio)}")

        if len(lista_envio) == 0:
            print("ℹ️ Nenhum contato elegível para envio neste momento.")
            print("📊 FINALIZADO")
            return

        enviados = 0
        registros = []

        for _, row in lista_envio.iterrows():
            email = row["email"]
            status, retorno = enviar_email(email, campanha)

            if status in [200, 201, 202]:
                enviados += 1
                print(f"✅ [{enviados}] ENVIADO COM SUCESSO: {email}")
                registros.append({
                    "email": email,
                    "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "campanha": campanha["nome"]
                })
            else:
                print(f"❌ ERRO: {email} - Status: {status} - Retorno: {retorno}")

            time.sleep(1)

        if enviados > 0:
            salvar_historico(registros)
            enviar_relatorio(enviados, campanha["nome"])

        print("📊 FINALIZADO")

    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")

if __name__ == "__main__":
    main()
