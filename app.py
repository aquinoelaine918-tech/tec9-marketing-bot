import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIÁVEIS DO RENDER
# =========================
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")  # ID do Instagram (1784....)

# =========================
# TESTE ONLINE
# =========================
@app.get("/")
def home():
    return "TEC9 BOT ONLINE ✅", 200


@app.get("/health")
def health():
    return jsonify(status="ok"), 200


# =========================
# VERIFICAÇÃO META
# =========================
@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado")
        return challenge, 200

    print("❌ Token inválido")
    return "erro", 403


# =========================
# RECEBE EVENTOS DO INSTAGRAM
# =========================
@app.post("/webhook")
def receive_webhook():
    data = request.get_json()
    print("📩 EVENTO RECEBIDO:", data)

    if data.get("object") != "instagram":
        return "ok", 200

    try:
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                message = messaging.get("message", {})
                text = message.get("text")

                if sender_id and text:
                    print(f"💬 Mensagem: {text}")
                    reply = "Olá 👋 Seja bem-vindo(a) à TEC9 Informática! Como posso ajudar você hoje?"
                    send_message(sender_id, reply)

    except Exception as e:
        print("❌ ERRO PROCESSANDO:", str(e))

    return "ok", 200


# =========================
# ENVIO DE MENSAGEM INSTAGRAM
# =========================
def send_message(recipient_id, text):

    if not META_ACCESS_TOKEN:
        print("❌ META_ACCESS_TOKEN não existe")
        return

    if not IG_USER_ID:
        print("❌ IG_USER_ID não existe")
        return

    url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("📤 RESPOSTA ENVIADA:", response.status_code, response.text)
    except Exception as e:
        print("❌ ERRO ENVIANDO:", str(e))
