import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

# =========================
# HOME
# =========================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE ✅", 200

# =========================
# WEBHOOK VERIFICATION
# =========================
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado")
        return challenge, 200
    return "Erro de verificação", 403

# =========================
# RECEBER MENSAGENS
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 EVENTO RECEBIDO:", data)

    try:
        for entry in data["entry"]:
            for msg in entry["messaging"]:
                if "message" in msg:

                    sender_id = msg["sender"]["id"]
                    text = msg["message"].get("text")

                    print("💬 Mensagem recebida:", text)

                    enviar_resposta(sender_id)

    except Exception as e:
        print("❌ ERRO:", e)

    return "ok", 200


# =========================
# ENVIAR RESPOSTA
# =========================
def enviar_resposta(sender_id):

    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={META_ACCESS_TOKEN}"

    payload = {
        "recipient": {"id": sender_id},
        "message": {"text": "Olá 👋 Sou o assistente TEC9. Recebi sua mensagem!"}
    }

    headers = {
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers)

    print("📤 RESPOSTA ENVIADA:", r.status_code, r.text)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
