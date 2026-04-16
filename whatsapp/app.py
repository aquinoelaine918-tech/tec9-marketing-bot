import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# =========================
# ROTA RAIZ (OBRIGATÓRIA)
# =========================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

# =========================
# HEALTH CHECK (IMPORTANTE)
# =========================
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# =========================
# VERIFICAÇÃO DO WEBHOOK
# =========================
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Erro de verificação", 403

# =========================
# RECEBER MENSAGENS
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Mensagem recebida:", data)
    return jsonify({"status": "ok"}), 200


# =========================
# START
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
