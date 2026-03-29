from flask import Flask, request
import requests

app = Flask(__name__)

VERIFY_TOKEN = "tec9token123"
ACCESS_TOKEN = "COLE_SEU_TOKEN_DA_META_AQUI"

@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge
    return "Erro", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print(data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            msg = value["messages"][0]
            from_number = msg["from"]
            phone_number_id = value["metadata"]["phone_number_id"]

            texto = msg["text"]["body"]

            resposta = f"Olá 👋 Recebi: {texto}"

            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"

            headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": "text",
                "text": {"body": resposta}
            }

            requests.post(url, headers=headers, json=payload)

    except Exception as e:
        print("Erro:", e)

    return "ok", 200
