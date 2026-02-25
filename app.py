from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "tec9_verify_2026"
PAGE_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")


@app.get("/")
def home():
    return "Tec bot rodando no Render ✅", 200


# 🔐 Verificação Meta
@app.get("/webhook")
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Token inválido", 403


# 📩 Receber mensagens
@app.post("/webhook")
def receive():
    data = request.get_json()
    print("EVENTO RECEBIDO:", data)

    if "entry" in data:
        for entry in data["entry"]:
            if "messaging" in entry:
                for event in entry["messaging"]:
                    if "message" in event and not event["message"].get("is_echo"):
                        sender_id = event["sender"]["id"]
                        send_reply(sender_id)

    return "ok", 200


# 🤖 Resposta automática
def send_reply(user_id):

    url = "https://graph.facebook.com/v19.0/me/messages"

    payload = {
        "recipient": {"id": user_id},
        "message": {
            "text": "Olá 👋 Seja bem-vindo(a) à TEC9 Informática! Como posso ajudar você hoje?"
        }
    }

    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }

    requests.post(url, json=payload, params=params)
