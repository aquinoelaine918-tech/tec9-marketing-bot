from flask import Flask, request
import requests

app = Flask(__name__)

# TOKEN DE VERIFICAÇÃO
VERIFY_TOKEN = "TEC9_TOKEN"

# TOKEN GERADO NO META
WHATSAPP_TOKEN = "COLE_SEU_TOKEN_AQUI"

# PHONE NUMBER ID
PHONE_NUMBER_ID = "1099079283287430"


@app.route("/")
def home():
    return "BOT ONLINE", 200


# VERIFICAÇÃO DO WEBHOOK
@app.route("/webhook", methods=["GET"])
def verify_webhook():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Erro de verificação", 403


# RECEBER MENSAGENS
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

                texto = message["text"]["body"]

                print(f"MENSAGEM DE {numero}: {texto}")

                responder_mensagem(numero, f"Você disse: {texto}")

    except Exception as erro:

        print("ERRO AO PROCESSAR:")
        print(erro)

    return "ok", 200


# ENVIAR RESPOSTA
def responder_mensagem(numero, mensagem):

    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"



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
