import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = "tec9token123"
WHATSAPP_TOKEN = "EAAK409sUM3YBRNCccW6ajBxCsWtW9A7qMZA2bWBqBP7Bl0aQkAiTZBwI43ZC4x1hhdej6aMVdedDlgX0amegPsUiIyOMIp6bxEZC4dDQzeahyRWcBGZCwHlMRmzEbd7ylSHbUTVoZCpExxLvd5coDBIyJWGOZCIVZAFfuBTSksJ8Y7OIEUxlNBlKH19XzQhz2GwDnuKIGvHPYltnLSQYQ1feITnUxjefZBuZCIkYRjEsG19Y0ZBy5ORQ2w2NKnHx6zlY4MFyLA5AOssVeHoUkOfz7mOqQZDZD"
PHONE_NUMBER_ID = "1099079283287430"

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "TEC9 BOT ONLINE 🚀"
    }), 200

# 🔹 VERIFICAÇÃO
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge
    return "Erro", 403

# 🔹 RECEBER E RESPONDER
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Evento recebido:", data)

    try:
        if "entry" in data:
            for entry in data["entry"]:
                for change in entry["changes"]:
                    value = change["value"]

                    if "messages" in value:
                        message = value["messages"][0]
                        from_number = message["from"]

                        if message["type"] == "text":
                            text = message["text"]["body"]

                            print("Mensagem:", text)

                            resposta = f"Olá! Você disse: {text}"
                            send_message(from_number, resposta)

    except Exception as e:
        print("Erro:", e)

    return "ok", 200

# 🔹 ENVIAR MENSAGEM
def send_message(to, message):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("Resposta envio:", response.text)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
