import pandas as pd
import requests
import time
import os
from datetime import datetime, timedelta

# ================= CONFIG =================

API_KEY = os.getenv("BREVO_API_KEY")

REMETENTE_EMAIL = os.getenv("REMETENTE_EMAIL")
REMETENTE_NOME = "TEC9 Informática"

EMAIL_RELATORIO = "comercial@tec9informatica.com.br"

# NOME EXATO DO ARQUIVO QUE APARECE NO SEU GITHUB
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
    # Pega a campanha baseada na semana do ano
    semana = datetime.now().isocalendar()[1]
    return CAMPANHAS[semana % len(CAMPANHAS)]


def carregar_clientes():
    # Lendo o arquivo CSV que está no seu GitHub
    df = pd.read_csv(ARQUIVO_CLIENTES)
    # Padroniza os nomes das colunas (tira espaços e deixa minúsculo)
    df.columns = [c.lower().strip() for c in df.columns]
    return df


def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return pd.DataFrame(columns=["email", "data", "campanha"])
    return pd.read_csv(ARQUIVO_HISTORICO)


def filtrar_clientes(df_clientes, df_historico):
    hoje = datetime.now()
    limite = hoy = hoje - timedelta(days=7)

    # Garante que a coluna de data seja lida corretamente
    df_historico["data"] = pd.to_datetime(df_historico["data"], errors="coerce")

    # Lista quem já recebeu e-mail nos últimos 7 dias
    enviados = df_historico[df_historico["data"] >= limite]["email"].unique()

    # Filtra quem ainda não recebeu
    df_filtrado = df_clientes[~df_clientes["email"].isin(enviados)]

    return df_filtrado.head(LIMITE_DIARIO)


def enviar_email(email, campanha):
    url = "https://brevo.com"

    headers = {
        "api-key": API_KEY,
        "content-type": "application/json"
    }

    payload = {
        "sender": {
            "name": REMETENTE_NOME,
            "email": REMETENTE_EMAIL
        },
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
    url = "https://brevo.com"

    headers = {
        "api-key": API_KEY,
        "content-type": "application/json"
    }

    html = f"""
    <h2>📊 Relatório TEC9</h2>
    <p><b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <p><b>Campanha:</b> {campanha_nome}</p>
    <p><b>Emails enviados hoje:</b> {enviados}</p>
    """

    payload = {
        "sender": {
            "name": REMETENTE_NOME,
            "email": REMETENTE_EMAIL
        },
        "to": [{"email": EMAIL_RELATORIO}],
        "subject": f"Relatório diário TEC9 - {campanha_nome}",
        "htmlContent": html
    }

    requests.post(url, json=payload, headers=headers)


# ================= EXECUÇÃO =================

def main():
    print("🚀 INICIANDO DISPARO AUTOMÁTICO TEC9")

    campanha = obter_campanha()
    print(f"📢 Campanha atual: {campanha['nome']}")

    try:
        # 1. Carrega os 120 contatos
        clientes = carregar_clientes()
        # 2. Carrega quem já recebeu antes
        historico = carregar_historico()

        # 3. Filtra para enviar apenas 5 por vez (limite de teste)
        lista_envio = filtrar_clientes(clientes, historico)

        print(f"📧 Total de envios programados para agora: {len(lista_envio)}")

        enviados = 0
        registros = []

        # 4. Loop de envio
        for i, row in lista_envio.iterrows():
            email = row["email"]

            status = enviar_email(email, campanha)

            if status in [200, 201, 202]:
                enviados += 1
                print(f"✅ [{enviados}] {email}")

                registros.append({
                    "email": email,
                    "data": datetime.now(),
                    "campanha": campanha["nome"]
                })
            else:
                print(f"❌ ERRO: {email} - Status: {status}")

            time.sleep(1) # Espera 1 segundo entre envios

        # 5. Salva quem recebeu e manda o relatório
        if enviados > 0:
            salvar_historico(registros)
            enviar_relatorio(enviados, campanha["nome"])

        print("📊 FINALIZADO")

    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")


if __name__ == "__main__":
    main()
