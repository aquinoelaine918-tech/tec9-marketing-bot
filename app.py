from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

VERIFY_TOKEN = "tec9token123"
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

@app.route("/", methods=["GET"])
def home():
    return "Bot online", 200

# VERIFICAÇÃO META
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Erro de verificação", 403

# RECEBER MENSAGEM (AQUI ESTAVA FALTANDO)
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        from_number = message["from"]
        text = message["text"]["body"]

        print("Mensagem recebida:", text)

        enviar_mensagem(from_number, f"Recebi: {text}")

    except:
        print("Evento sem mensagem")

    return "ok", 200


def enviar_mensagem(numero, texto):
    url = "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }

    requests.post(url, headers=headers, json=payload)


if __name__ == "__main__":
    app.run()
