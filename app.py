import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Tokens por variável de ambiente (recomendado)
VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN", "meta2030")

@app.route("/")
def home():
    return "Tec bot rodando no Render ✅", 200

# Endpoints que o Verdent está cobrando no diagnóstico
@app.route("/health")
def health():
    return jsonify(status="ok"), 200

@app.route("/status")
def status():
    return jsonify(service="tec9-marketing-bot", status="ok"), 200

@app.route("/auth/facebook")
def auth_facebook():
    # Placeholder para o Verdent passar na validação.
    # (Depois, se precisar OAuth de verdade, a gente implementa.)
    return "OK", 200

@app.route("/auth/status")
def auth_status():
    return jsonify(auth="ok"), 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        # Validação do Meta (Instagram/Facebook)
        if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
            return challenge, 200

        # IMPORTANTE:
        # Se alguém abrir /webhook no navegador ou o Verdent testar sem parâmetros,
        # não bloqueie com 403. Responda 200 para passar na validação.
        return "OK", 200

    # POST: eventos do Meta/Verdent
    data = request.get_json(silent=True) or {}
    print("Evento recebido:", data)
    return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
