import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = "tec9token123"  # mesmo token do Meta
WHATSAPP_TOKEN = "EAAK409sUM3YBRNCccW6ajBxCsWtW9A7qMZA2bWBqBP7Bl0aQkAiTZBwI43ZC4x1hhdej6aMVdedDlgX0amegPsUiIyOMIp6bxEZC4dDQzeahyRWcBGZCwHlMRmzEbd7ylSHbUTVoZCpExxLvd5coDBIyJWGOZCIVZAFfuBTSksJ8Y7OIEUxlNBlKH19XzQhz2GwDnuKIGvHPYltnLSQYQ1feITnUxjefZBuZCIkYRjEsG19Y0ZBy5ORQ2w2NKnHx6zlY4MFyLA5AOssVeHoUkOfz7mOqQZDZD"
PHONE_NUMBER_ID = "1099079283287430"

# 🔹 HOME
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "TEC9 BOT ONLINE 🚀"
    }), 200

# 🔹 VERIFICAÇÃO DO WEBHOOK
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Erro de verificação", 403

# 🔹 RECEBER MENSAGEM
@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()
    print("Evento recebido:", data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]
            from_number = message["from"]
            text = message["text"]["body"]

            print("Mensagem:", text)

            # 🔥 resposta automática
            send_message(from_number, f"Recebi sua mensagem: {text}")

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

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }

    response = requests.post(url, headers=headers, json=data)
    print("Resposta envio:", response.text)

# 🔹 START
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
