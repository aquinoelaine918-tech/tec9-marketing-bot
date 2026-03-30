import os
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "tec9token123")


@app.route("/", methods=["GET"])
def home():
    return "Bot online", 200


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # Validação do webhook pela Meta
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge, 200
        return "Erro de verificação", 403

    # Recebimento de eventos/mensagens da Meta
    if request.method == "POST":
        data = request.get_json(silent=True)

        # Mostra no log do Railway o que chegou
        print("Webhook recebido:", data, flush=True)

        # Meta só precisa de resposta 200
        return jsonify({"status": "received"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
