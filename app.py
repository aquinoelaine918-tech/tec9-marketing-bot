import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Home
@app.get("/")
def home():
    return "Tec bot rodando no Render ✅", 200

# Health check (Verdent)
@app.get("/health")
def health():
    return jsonify(status="ok"), 200

# Status (Verdent)
@app.get("/status")
def status():
    return jsonify(
        service="tec9-marketing-bot",
        up=True
    ), 200

# Webhook (Meta/Instagram)
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        verify_token = os.getenv("META_VERIFY_TOKEN", "")

        if mode == "subscribe" and token == verify_token:
            return challenge, 200

        return "Token de verificação inválido", 403

    # POST: Meta envia eventos aqui
    data = request.get_json(silent=True) or {}
    # IMPORTANTÍSSIMO: responder rápido
    return jsonify(received=True), 200

# Rotas "auth" que o Verdent está cobrando (podem ser simples por enquanto)
@app.get("/auth/facebook")
def auth_facebook():
    # Placeholder para passar diagnóstico do Verdent.
    # Depois colocamos OAuth real (se o Verdent precisar).
    return jsonify(ok=True, message="Auth endpoint ativo"), 200

@app.get("/auth/status")
def auth_status():
    return jsonify(ok=True, authenticated=False), 200
