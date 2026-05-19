from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "TEC9_TOKEN"

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")

PHONE_NUMBER_ID = "1099079283287430"


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

        if "messages" not in value:
            return "ok", 200

        message = value["messages"][0]

        tipo = message.get("type")

        print(f"TIPO: {tipo}")

        # ============================================
        # IGNORA TIPOS NÃO SUPORTADOS
        # ============================================

        if tipo != "text":

            print("Mensagem ignorada")

            return "ok", 200

        numero = message["from"]

        texto = message["text"]["body"]

        print(f"MENSAGEM DE {numero}")
        print(texto)

        enviar_mensagem(numero, f"Você disse: {texto}")

        return "ok", 200

    except Exception as erro:

        print("ERRO:")
        print(erro)

        return "erro", 500


def enviar_mensagem(numero, mensagem):

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

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    print(response.status_code)
    print(response.text)


if __name__ == "__main__":

    porta = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=porta
    )
