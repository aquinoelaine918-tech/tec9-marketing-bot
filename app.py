from flask import Flask, request
import os
import requests

app = Flask(__name__)

VERIFY_TOKEN = "tec9token123"
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


@app.route("/", methods=["GET"])
def home():
    return "Bot online", 200


@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Erro de verificação", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Recebido:", data)

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" in value:
            message = value["messages"][0]
            from_number = message["from"]

            texto = "mensagem recebida"
            if "text" in message:
                texto = message["text"]["body"]

            enviar_mensagem(from_number, f"Recebi: {texto}")

    except Exception as e:
        print("Erro no webhook:", str(e))

    return "ok", 200


def enviar_mensagem(numero, texto):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

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

    r = requests.post(url, headers=headers, json=payload)
    print("STATUS META:", r.status_code)
    print("RESPOSTA META:", r.text)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
