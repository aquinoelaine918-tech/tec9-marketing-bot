from flask import Flask, request
app = Flask(__name__)

VERIFY_TOKEN = "tec9_verify_2026"


@app.get("/")
def home():
    return "Tec bot rodando no Render ✅", 200


@app.get("/webhook")
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Token de verificação inválido", 403
