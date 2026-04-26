import pandas as pd
import requests
import time
import os
from datetime import datetime, timedelta

# ================= CONFIGURAÇÕES =================

# No Railway, certifique-se de que estas variáveis de ambiente estão preenchidas
API_KEY = (os.getenv("BREVO_API_KEY") or "").strip()
REMETENTE_EMAIL = (os.getenv("REMETENTE_EMAIL") or "comercial@tec9informatica.com.br").strip()
REMETENTE_NOME = "TEC9 Informática"
EMAIL_RELATORIO = (os.getenv("EMAIL_RELATORIO") or "comercial@tec9informatica.com.br").strip()

# ID do modelo que você criou na aba "Modelos" da Brevo
ID_MODELO_BREVO = 5 

ARQUIVOS_CLIENTES_POSSIVEIS = [
    "Clientes_TEC9.xlsx.csv",
    "Clientes_TEC9.csv",
    "Clientes_TEC9.xlsx",
]

ARQUIVO_HISTORICO = "historico_envios.csv"
LIMITE_DIARIO = 300

# URL CORRIGIDA PARA A API V3
URL_ENVIO_BREVO = "https://brevo.com"

# ================= FUNÇÕES =================

def validar_configuracoes():
    if not API_KEY:
        raise ValueError("BREVO_API_KEY não configurada no Railway.")
    if not REMETENTE_EMAIL:
        raise ValueError("REMETENTE_EMAIL não configurada.")

def encontrar_arquivo_clientes():
    for arquivo in ARQUIVOS_CLIENTES_POSSIVEIS:
        if os.path.exists(arquivo):
            return arquivo
    raise FileNotFoundError("Nenhum arquivo de clientes encontrado (Excel ou CSV).")

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

def enviar_email(email):
    headers = {
        "accept": "application/json", 
        "api-key": API_KEY, 
        "content-type": "application/json"
    }
    
    # Chama o templateId para usar o design da Brevo com anexo
    payload = {
        "sender": {"name": REMETENTE_NOME, "email": REMETENTE_EMAIL},
        "to": [{"email": email}],
        "templateId": ID_MODELO_BREVO
    }
    
    try:
        response = requests.post(URL_ENVIO_BREVO, json=payload, headers=headers, timeout=30)
        return response.status_code, response.text
    except Exception as e:
        return None, str(e)

def salvar_historico_unico(email):
    novo_registro = pd.DataFrame([{
        "email": email,
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "campanha": f"Template_{ID_MODELO_BREVO}"
    }])
    if os.path.exists(ARQUIVO_HISTORICO):
        novo_registro.to_csv(ARQUIVO_HISTORICO, mode='a', header=False, index=False)
    else:
        novo_registro.to_csv(ARQUIVO_HISTORICO, index=False)

def enviar_relatorio(enviados):
    headers = {"accept": "application/json", "api-key": API_KEY, "content-type": "application/json"}
    html = f"<h2>📊 Relatório TEC9</h2><p>E-mails enviados hoje: <b>{enviados}</b> usando o modelo {ID_MODELO_BREVO}.</p>"
    payload = {
        "sender": {"name": REMETENTE_NOME, "email": REMETENTE_EMAIL},
        "to": [{"email": EMAIL_RELATORIO}],
        "subject": f"Relatório de Disparo - {datetime.now().strftime('%d/%m/%Y')}",
        "htmlContent": html
    }
    requests.post(URL_ENVIO_BREVO, json=payload, headers=headers)

# ================= EXECUÇÃO =================

def main():
    print(f"🚀 INICIANDO DISPARO TEC9 - MODELO ID: {ID_MODELO_BREVO}")
    try:
        validar_configuracoes()
        clientes = carregar_clientes()
        historico = carregar_historico()
        lista_envio = filtrar_clientes(clientes, historico)

        if len(lista_envio) == 0:
            print("ℹ️ Nenhum contato novo para enviar hoje (filtro de 7 dias ativo).")
            return

        enviados = 0
        for _, row in lista_envio.iterrows():
            email = row["email"]
            status, retorno = enviar_email(email)

            if status in [200, 201, 202]:
                enviados += 1
                print(f"✅ [{enviados}] ENVIADO: {email}")
                salvar_historico_unico(email)
            else:
                print(f"❌ ERRO no e-mail {email}: Status {status} - {retorno}")

            time.sleep(2) # Pausa para evitar bloqueios de spam

        if enviados > 0:
            enviar_relatorio(enviados)
        print(f"📊 FINALIZADO. Total de envios realizados: {enviados}")

    except Exception as e:
        print(f"❌ ERRO CRÍTICO NO SCRIPT: {e}")

if __name__ == "__main__":
    main()
