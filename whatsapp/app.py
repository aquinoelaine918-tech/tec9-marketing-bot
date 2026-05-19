from flask import Flask, request
import requests
import os

app = Flask(__name__)

# =========================================================
# CONFIGURAÇÕES
# =========================================================

VERIFY_TOKEN = "TEC9_TOKEN"

WHATSAPP_TOKEN = os.getenv("META_ACCESS_TOKEN")

PHONE_NUMBER_ID = "1099079283287430"

WHATSAPP_ESPECIALISTA = "https://wa.me/5511977315223"

SITE_BUSCA = "https://tec9informatica.com.br/busca?q="

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return "TEC9 BOT ONLINE 🚀", 200

# =========================================================
# VERIFICAÇÃO WEBHOOK
# =========================================================

@app.route("/webhook", methods=["GET"])
def verify_webhook():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Erro de verificação", 403

# =========================================================
# RECEBER MENSAGEM
# =========================================================

@app.route("/webhook", methods=["POST"])
def receber_mensagem():

    data = request.get_json()

    print("\n================================================")
    print("EVENTO RECEBIDO:")
    print(data)
    print("================================================\n")

    try:

        entry = data["entry"][0]

        changes = entry["changes"][0]

        value = changes["value"]

        messages = value.get("messages")

        if messages:

            message = messages[0]

            numero = message["from"]

            tipo = message["type"]

            print(f"TIPO: {tipo}")
            print(f"NUMERO: {numero}")

            if tipo == "text":

                texto_original = message["text"]["body"].strip()

                texto = texto_original.lower()

                print(f"MENSAGEM: {texto}")

                # =====================================================
                # MENU INICIAL
                # =====================================================

                if texto in [
                    "oi",
                    "ola",
                    "olá",
                    "bom dia",
                    "boa tarde",
                    "boa noite",
                    "menu"
                ]:

                    menu = (
                        "Olá 👋 Seja bem-vindo(a) à *TEC9 Informática* 🚀\n\n"
                        "Escolha uma opção:\n\n"
                        "1️⃣ Pessoa Jurídica\n"
                        "2️⃣ Pessoa Física\n"
                        "3️⃣ Upgrade / SSD / peças\n\n"
                        "Ou digite diretamente o produto que procura 👇"
                    )

                    responder_mensagem(numero, menu)

                # =====================================================
                # PESSOA JURÍDICA
                # =====================================================

                elif texto == "1":

                    resposta_pj = (
                        "🏢 *Atendimento Pessoa Jurídica*\n\n"
                        "Para agilizar seu atendimento, envie:\n\n"
                        "📌 CNPJ\n"
                        "📌 Nome do responsável\n"
                        "📌 E-mail\n"
                        "📌 Produto desejado\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF\n\n"
                        "Nossa equipe comercial dará continuidade ao atendimento 🚀"
                    )

                    responder_mensagem(numero, resposta_pj)

                # =====================================================
                # PESSOA FÍSICA
                # =====================================================

                elif texto == "2":

                    resposta_pf = (
                        "👤 *Atendimento Pessoa Física*\n\n"
                        "Para prosseguirmos com seu atendimento, envie:\n\n"
                        "📌 Nome\n"
                        "📌 Produto desejado\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF\n\n"
                        "Nossa equipe comercial dará continuidade ao atendimento 🚀"
                    )

                    responder_mensagem(numero, resposta_pf)

                # =====================================================
                # UPGRADE / PEÇAS
                # =====================================================

                elif texto == "3":

                    resposta_upgrade = (
                        "🔧 *Upgrade e Peças*\n\n"
                        "Digite o produto desejado.\n\n"
                        "Exemplos:\n"
                        "SSD\n"
                        "Memória\n"
                        "Fonte\n"
                        "Notebook\n"
                        "Processador\n"
                        "Placa de vídeo"
                    )

                    responder_mensagem(numero, resposta_upgrade)

                # =====================================================
                # CLIENTE QUENTE
                # =====================================================

                elif any(p in texto for p in [
                    "comprar",
                    "orcamento",
                    "orçamento",
                    "desconto",
                    "pedido",
                    "fechar",
                    "pix",
                    "urgente"
                ]):

                    mensagem = (
                        "🔥 Identificamos interesse comercial.\n\n"
                        "Para agilizar seu atendimento e verificar condições especiais, "
                        "fale diretamente com nossa especialista 👇\n\n"
                        f"{WHATSAPP_ESPECIALISTA}"
                    )

                    responder_mensagem(numero, mensagem)

                # =====================================================
                # EMPRESA AUTOMÁTICO
                # =====================================================

                elif any(p in texto for p in [
                    "empresa",
                    "cnpj",
                    "corporativo",
                    "servidor",
                    "infraestrutura"
                ]):

                    mensagem = (
                        "🏢 Atendimento corporativo identificado.\n\n"
                        "Para atendimento especializado 👇\n\n"
                        f"{WHATSAPP_ESPECIALISTA}"
                    )

                    responder_mensagem(numero, mensagem)

                # =====================================================
                # BUSCA SIMPLES
                # =====================================================

                else:

                    busca = texto.replace(" ", "+")

                    link = f"{SITE_BUSCA}{busca}"

                    mensagem = (
                        f"🔎 Encontrei opções relacionadas a: *{texto_original}*\n\n"
                        f"Veja aqui:\n"
                        f"{link}\n\n"
                        f"Se desejar atendimento especializado 👇\n"
                        f"{WHATSAPP_ESPECIALISTA}"
                    )

                    responder_mensagem(numero, mensagem)

    except Exception as erro:

        print("\n================================================")
        print("ERRO AO PROCESSAR:")
        print(erro)
        print("================================================\n")

    return "ok", 200

# =========================================================
# ENVIAR MENSAGEM
# =========================================================

def responder_mensagem(numero, mensagem):

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": mensagem
        }
    }

    try:

        resposta = requests.post(
            url,
            headers=headers,
            json=payload
        )

        print("\n================================================")
        print(f"STATUS ENVIO: {resposta.status_code}")
        print(f"RESPOSTA ENVIO: {resposta.text}")
        print("================================================\n")

    except Exception as erro:

        print("\n================================================")
        print("ERRO AO ENVIAR:")
        print(erro)
        print("================================================\n")

# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    porta = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=porta
    )
