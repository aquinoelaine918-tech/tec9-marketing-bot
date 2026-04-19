import os
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = "abc123"  # coloque o mesmo token do Meta aqui

# 🔹 HOME
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "TEC9 BOT ONLINE 🚀"
    }), 200

# 🔹 HEALTH CHECK
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# 🔹 VERIFICAÇÃO DO WEBHOOK (Meta usa GET)
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Erro de verificação", 403

# 🔹 RECEBER MENSAGENS (Meta usa POST)
@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()
    print("Evento recebido:", data)

    return "ok", 200

# 🔹 START
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
