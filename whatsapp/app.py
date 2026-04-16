import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIÁVEIS
# =========================
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# =========================
# ROTA PRINCIPAL (OBRIGATÓRIA)
# =========================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "message": "TEC9 BOT ONLINE 🚀"
    }), 200

# =========================
# HEALTH CHECK
# =========================
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# =========================
# WEBHOOK VERIFICAÇÃO (META)
# =========================
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verificado com sucesso")
        return challenge, 200
    else:
        return "Erro na verificação", 403

# =========================
# RECEBER MENSAGENS
# =========================
@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()

    print("Mensagem recebida:")
    print(data)

    return "ok", 200

# =========================
# START LOCAL
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
