import pandas as pd
import requests
import time
import os
from datetime import datetime, timedelta

# ================= CONFIGURAÇÕES =================

API_KEY = os.getenv("BREVO_API_KEY")
REMETENTE_EMAIL = os.getenv("REMETENTE_EMAIL")
REMETENTE_NOME = "TEC9 Informática"
EMAIL_RELATORIO = "comercial@tec9informatica.com.br"

# Nome exato que aparece na lateral do seu GitHub
ARQUIVO_CLIENTES = "Clientes_TEC9.xlsx.csv"
ARQUIVO_HISTORICO = "historico_envios.csv"

# Limite de 5 para o teste de agora (depois mude para 300)
LIMITE_DIARIO = 5

# ================= CAMPANHAS =================

CAMPANHAS = [
    {
        "nome": "SEMANA_1",
        "assunto": "Sua empresa pode estar gastando mais do que deveria com TI",
        "html": "<p>Olá, tudo bem?<br><br>Podemos ajudar sua empresa a reduzir custos com tecnologia e melhorar desempenho.<br><br>Fale com a TEC9.</p>"
    }
]

# ================= FUNÇÕES =================

def obter_campanha():
    semana = datetime.now().isocalendar()[1]
    return CAMPANHAS[semana % len(CAMPANHAS)]

def carregar_clientes():
    # Lendo o arquivo CSV que está no seu GitHub
    df = pd.read_csv(ARQUIVO_CLIENTES)
    df.columns = [c.lower().strip() for c in df.columns]
    return df

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return pd.DataFrame(columns=["email", "data", "campanha"])
    return pd.read_csv(ARQUIVO_HISTORICO)

def filtrar_clientes(df_clientes, df_historico):
    hoje = datetime.now()
    limite = hoje - timedelta(days=7)
    df_historico["data"] = pd.to_datetime(df_historico["data"], errors="coerce")
    enviados = df_historico[df_historico["data"] >= limite]["email"].unique()
    df_filtrado = df_clientes[~df_clientes["email"].isin(enviados)]
    return df_filtrado.head(LIMITE_DIARIO)

def enviar_email(email, campanha):
    # URL CORRIGIDA PARA EVITAR ERRO 404
    url = "https://brevo.com"
    headers = {
        "api-key": API_KEY,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": REMETENTE_NOME, "email": REMETENTE_EMAIL},
        "to": [{"email": email}],
        "subject": campanha["assunto"],
        "htmlContent": campanha["html"]
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code
    except Exception as e:
        print(f"Erro ao enviar para {email}: {e}")
        return None

def salvar_historico(registros):
    df = pd.DataFrame(registros)
    if os.path.exists(ARQUIVO_HISTORICO):
        df_antigo = pd.read_csv(ARQUIVO_HISTORICO)
        df = pd.concat([df_antigo, df])
    df.to_csv(ARQUIVO_HISTORICO, index=False)

def enviar_relatorio(enviados, campanha_nome):
    # URL CORRIGIDA PARA EVITAR ERRO 404
    url = "https://brevo.com"
    headers = {
        "api-key": API_KEY,
        "content-type": "application/json"
    }
    html = f"<h2>📊 Relatório TEC9</h2><p><b>Emails enviados hoje:</b> {enviados}</p>"
    payload = {
        "sender": {"name": REMETENTE_NOME, "email": REMETENTE_EMAIL},
        "to": [{"email": EMAIL_RELATORIO}],
        "subject": f"Relatório diário TEC9 - {campanha_nome}",
        "htmlContent": html
    }
    requests.post(url, json=payload, headers=headers)

# ================= EXECUÇÃO =================

def main():
    print("🚀 INICIANDO DISPARO AUTOMÁTICO TEC9")
    campanha = obter_campanha()
    try:
        clientes = carregar_clientes()
        historico = carregar_historico()
        lista_envio = filtrar_clientes(clientes, historico)
        print(f"📧 Total de envios para agora: {len(lista_envio)}")
        enviados = 0
        registros = []
        for i, row in lista_envio.iterrows():
            email = row["email"]
            status = enviar_email(email, campanha)
            if status in [200, 201, 202]:
                enviados += 1
                print(f"✅ [{enviados}] {email}")
                registros.append({"email": email, "data": datetime.now(), "campanha": campanha["nome"]})
            else:
                print(f"❌ ERRO: {email} - Status: {status}")
            time.sleep(1)
        if enviados > 0:
            salvar_historico(registros)
            enviar_relatorio(enviados, campanha["nome"])
        print("📊 FINALIZADO")
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")

if __name__ == "__main__":
    main()
