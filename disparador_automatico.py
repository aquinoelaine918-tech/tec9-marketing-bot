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

ARQUIVOS_CLIENTES_POSSIVEIS = [
    "Clientes_TEC9.xlsx.csv",
    "Clientes_TEC9.csv",
    "Clientes_TEC9.xlsx",
]

ARQUIVO_HISTORICO = "historico_envios.csv"

# NOVO LIMITE CONFIGURADO
LIMITE_DIARIO = 300

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
    raise FileNotFoundError("Nenhum arquivo de clientes encontrado.")

def carregar_clientes():
    arquivo = encontrar_arquivo_clientes()
    if arquivo.lower().endswith(".xlsx"):
        df = pd.read_excel(arquivo)
    else:
        df = pd.read_csv(arquivo, on_bad_lines='skip', sep=',', engine='python')
    
    df.columns = [str(c).lower().strip() for c in df.columns]
    df["email"] = df["email"].astype(str).str.strip().str.lower()
    df = df[df["email"].str.contains("@", na=False)].drop_duplicates(subset=["email"])
    return df

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return pd.DataFrame(columns=["email", "data", "campanha"])
    try:
        df = pd.read_csv(ARQUIVO_HISTORICO)
        df["email"] = df["email"].astype(str).str.strip().str.lower()
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        return df
    except:
        return pd.DataFrame(columns=["email", "data", "campanha"])

def filtrar_clientes(df_clientes, df_historico):
    hoje = datetime.now()
    limite = hoje - timedelta(days=7)
    enviados_recentes = df_historico[df_historico["data"] >= limite]["email"].unique()
    df_filtrado = df_clientes[~df_clientes["email"].isin(enviados_recentes)]
    return df_filtrado.head(LIMITE_DIARIO)

def enviar_email(email, campanha):
    headers = {"accept": "application/json", "api-key": API_KEY, "content-type": "application/json"}
    payload = {
        "sender": {"name": REMETENTE_NOME, "email": REMETENTE_EMAIL},
        "to": [{"email": email}],
        "subject": campanha["assunto"],
        "htmlContent": campanha["html"]
    }
    try:
        response = requests.post(URL_ENVIO_BREVO, json=payload, headers=headers, timeout=30)
        return response.status_code, response.text
    except Exception as e:
        return None, str(e)

def salvar_historico_unico(email, campanha_nome):
    """Salva no histórico imediatamente após o envio de cada e-mail"""
    novo_registro = pd.DataFrame([{
        "email": email,
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "campanha": campanha_nome
    }])
    if os.path.exists(ARQUIVO_HISTORICO):
        novo_registro.to_csv(ARQUIVO_HISTORICO, mode='a', header=False, index=False)
    else:
        novo_registro.to_csv(ARQUIVO_HISTORICO, index=False)

def enviar_relatorio(enviados, campanha_nome):
    headers = {"accept": "application/json", "api-key": API_KEY, "content-type": "application/json"}
    html = f"<h2>📊 Relatório TEC9</h2><p>E-mails enviados agora: {enviados}</p>"
    payload = {
        "sender": {"name": REMETENTE_NOME, "email": REMETENTE_EMAIL},
        "to": [{"email": EMAIL_RELATORIO}],
        "subject": f"Relatório TEC9 - {campanha_nome}",
        "htmlContent": html
    }
    requests.post(URL_ENVIO_BREVO, json=payload, headers=headers)

# ================= EXECUÇÃO =================

def main():
    print("🚀 INICIANDO DISPARO AUTOMÁTICO TEC9")
    try:
        validar_configuracoes()
        campanha = obter_campanha()
        clientes = carregar_clientes()
        historico = carregar_historico()
        lista_envio = filtrar_clientes(clientes, historico)

        if len(lista_envio) == 0:
            print("ℹ️ Nenhum contato novo para enviar.")
            return

        enviados = 0
        for _, row in lista_envio.iterrows():
            email = row["email"]
            status, retorno = enviar_email(email, campanha)

            if status in [200, 201, 202]:
                enviados += 1
                print(f"✅ [{enviados}] ENVIADO: {email}")
                salvar_historico_unico(email, campanha["nome"]) # SALVAMENTO IMEDIATO
            else:
                print(f"❌ ERRO: {email} - Status: {status}")

            time.sleep(1.5) # Pausa leve entre envios

        if enviados > 0:
            enviar_relatorio(enviados, campanha["nome"])
        print("📊 FINALIZADO")

    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")

if __name__ == "__main__":
    main()
