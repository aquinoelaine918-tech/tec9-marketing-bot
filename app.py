import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Tec bot rodando no Render ✅", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        # Ajustado para o token 'meta2030'
        if mode == "subscribe" and token == "meta2030":
            return challenge, 200
        return "Token de verificação inválido", 403

    if request.method == "POST":
        data = request.get_json()
        print("Evento recebido:", data)
        return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
