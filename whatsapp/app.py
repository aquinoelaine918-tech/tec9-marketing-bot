import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ================================
# VARIÁVEIS DE AMBIENTE
# ================================

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "123456")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ================================
# ROTAS DE TESTE (IMPORTANTES)
# ================================

@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "bot": "TEC9",
        "openai": "ok" if OPENAI_API_KEY else "sem chave"
    }), 200


# ================================
# WEBHOOK VERIFICAÇÃO
# ================================

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    try:
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200

        return "Token inválido", 403

    except Exception as e:
        print("Erro verify_webhook:", e)
        return "Erro", 500


# ================================
# RECEBER MENSAGEM WHATSAPP
# ================================

@app.route("/webhook", methods=["POST"])
def receive_message():
    try:
        data = request.get_json()
        print("Mensagem recebida:", data)

        return "EVENT_RECEIVED", 200

    except Exception as e:
        print("Erro receive_message:", e)
        return "Erro", 500


# ================================
# START APP
# ================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
