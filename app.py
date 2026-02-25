from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 🔐 TOKENS
VERIFY_TOKEN = "tec9_verify_2026"
PAGE_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")


# ✅ TESTE ONLINE
@app.get("/")
def home():
    return "Tec bot rodando no Render ✅", 200


# 🔐 VERIFICAÇÃO META
@app.get("/webhook")
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Token de verificação inválido", 403


# 📩 RECEBER MENSAGENS INSTAGRAM
@app.post("/webhook")
def receive():
    data = request.get_json()
    print("EVENTO RECEBIDO:", data)

    if "entry" in data:
        for entry in data["entry"]:
            for messaging in entry.get("messaging", []):

                sender_id = messaging["sender"]["id"]

                # ignora mensagens enviadas pelo próprio bot
                if messaging.get("message", {}).get("is_echo"):
                    continue

                send_reply(sender_id)

    return "ok", 200


# 🤖 RESPOSTA AUTOMÁTICA TEC9
def send_reply(user_id):

    url = "https://graph.facebook.com/v19.0/me/messages"

    payload = {
        "recipient": {"id": user_id},
        "message": {
            "text": "Olá 👋 Seja bem-vindo(a) à TEC9 Informática!\n\nComo posso ajudar você hoje?\n\n1️⃣ Orçamento\n2️⃣ Produtos\n3️⃣ Suporte\n4️⃣ Falar com especialista"
        }
    }

    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }

    response = requests.post(url, json=payload, params=params)
    print("RESPOSTA ENVIADA:", response.text)
