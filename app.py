import os
import urllib.parse
from flask import Flask, request, jsonify, redirect

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
    return jsonify(service="tec9-marketing-bot", up=True), 200

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
    _data = request.get_json(silent=True) or {}
    # IMPORTANTÍSSIMO: responder rápido
    return jsonify(received=True), 200

# OAuth Facebook (real)
@app.get("/auth/facebook")
def auth_facebook():
    # Sem ?start=true: só confirma que o endpoint existe
    start = request.args.get("start")
    if start != "true":
        return jsonify(ok=True, message="Auth endpoint ativo"), 200

    app_id = os.getenv("FACEBOOK_APP_ID")
    if not app_id:
        return jsonify(ok=False, error="Faltando variável FACEBOOK_APP_ID no Render"), 500

    redirect_uri = "https://tec9-marketing-bot.onrender.com/auth/callback"

    # Permissões que o Verdent costuma exigir para IG
    scope = "pages_manage_metadata,pages_manage_engagement,pages_read_engagement,pages_show_list"

    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
    }

    url = "https://www.facebook.com/v19.0/dialog/oauth?" + urllib.parse.urlencode(params)
    return redirect(url)

# Callback (por enquanto só confirma que voltou)
@app.get("/auth/callback")
def auth_callback():
    # Aqui virá ?code=...
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return jsonify(ok=False, error=error, details=request.args.to_dict()), 400

    if not code:
        return jsonify(ok=False, error="Callback sem code", details=request.args.to_dict()), 400

    # IMPORTANTE:
    # Por enquanto só confirmamos que o Facebook retornou o code.
    # Próximo passo (se precisar): trocar o code por access_token e salvar no Render/DB.
    return jsonify(ok=True, message="Callback recebido com sucesso", has_code=True), 200

# Status do OAuth (não pode ser fixo false)
@app.get("/auth/status")
def auth_status():
    return jsonify(ok=True, authenticated=False), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
