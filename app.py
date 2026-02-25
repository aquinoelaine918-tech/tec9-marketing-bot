from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "tec9_verify_2026"
PAGE_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")

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


# 📩 RECEBER MENSAGENS
@app.post("/webhook")
def receive():

    data = request.get_json()
    print("EVENTO RECEBIDO:", data)

    if "entry" in data:
        for entry in data["entry"]:
            for change in entry.get("changes", []):
                value = change.get("value", {})

                if "messages" in value:
                    for message in value["messages"]:
                        sender_id = message["from"]["id"]
                        send_reply(sender_id)

    return "ok", 200


# 🤖 RESPOSTA AUTOMÁTICA
def send_reply(user_id):

    url = "https://graph.facebook.com/v19.0/me/messages"

    payload = {
        "recipient": {"id": user_id},
        "message": {"text": "Olá 👋 Seja bem-vindo(a) à TEC9 Informática! Como posso ajudar você hoje?"}
    }

    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }

    requests.post(url, json=payload, params=params)
