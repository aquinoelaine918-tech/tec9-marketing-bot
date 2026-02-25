import os
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = (
    os.getenv("META_VERIFY_TOKEN")
    or os.getenv("VERIFY_TOKEN")
    or ""
)

@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Token de verificação inválido", 403
