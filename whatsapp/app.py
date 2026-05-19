from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "TEC9_TOKEN"

WHATSAPP_TOKEN = os.getenv("META_ACCESS_TOKEN")

PHONE_NUMBER_ID = "1099079283287430"


@app.route("/")
def home():
    return "BOT ONLINE", 200


@app.route("/webhook", methods=["GET"])
def verify_webhook():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Erro de verificação", 403


@app.route("/webhook", methods=["POST"])
def receber_mensagem():

    data = request.get_json()

    print("EVENTO RECEBIDO:")
    print(data)

    try:

        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages = value.get("messages")

        if messages:

            message = messages[0]

            numero = message["from"]

            tipo = message["type"]

            print(f"TIPO: {tipo} DE: {numero}")

            if tipo == "text":

                texto = message["text"]["body"].strip()

                print(f"MENSAGEM DE {numero}: {texto}")

                # ========================================================
                # SEU FLUXO DE ATENDIMENTO INTEGRADO AQUI
                # ========================================================
                if texto == "1":
                    # Bloco 2: Atendimento Pessoa Jurídica
                    resposta_pj = (
                        "🏢 *Atendimento Pessoa Jurídica*\n\n"
                        "Para agilizar seu orçamento e atendimento corporativo, envie as informações abaixo:\n\n"
                        "📌 CNPJ\n"
                        "📌 Nome do comprador/responsável\n"
                        "📌 E-mail corporativo\n"
                        "📌 Produto ou solução desejada\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF para entrega\n\n"
                        "Após o envio, nossa equipe comercial dará continuidade ao atendimento 🚀"
                    )
                    responder_mensagem(numero, resposta_pj)

                elif texto == "2":
                    # Bloco 3: Atendimento Pessoa Física
                    resposta_pf = (
                        "👤 *Atendimento Pessoa Física*\n\n"
                        "Para prosseguirmos com seu atendimento, envie:\n\n"
                        "📌 Nome\n"
                        "📌 Produto desejado\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF para entrega\n"
                        "📌 E-mail para envio da proposta (opcional)\n\n"
                        "Após o envio, nossa equipe comercial dará continuidade ao atendimento 🚀"
                    )
                    responder_mensagem(numero, resposta_pf)

                else:
                    # Bloco 1: Menu Inicial para qualquer outra mensagem
                    menu_inicial = (
                        "Olá, seja bem-vindo à TEC9 Informática 🚀\n\n"
                        "Para iniciarmos seu atendimento, selecione uma opção:\n\n"
                        "1️⃣ Pessoa Jurídica\n"
                        "2️⃣ Pessoa Física\n\n"
                        "Digite o número correspondente 👇"
                    )
                    responder_mensagem(numero, menu_inicial)

    except Exception as erro:

        print("ERRO AO PROCESSAR:")
        print(erro)

    return "ok", 200


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

    resposta = requests.post(
        url,
        headers=headers,
        json=payload
    )

    print(f"STATUS ENVIO: {resposta.status_code}")
    print(f"RESPOSTA ENVIO: {resposta.text}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
