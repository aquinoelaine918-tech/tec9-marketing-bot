import os
import urllib.parse
import requests
from flask import Flask, request, jsonify, redirect

app = Flask(__name__)

# ---------------- CONFIG ----------------
# Render ENV (obrigatórios)
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "").strip()
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "").strip()

# IMPORTANTÍSSIMO:
# Seu Render tem "FACEBOOK_REDIRECT_URI", mas seu código usava "OAUTH_REDIRECT_URI".
# Aqui aceitamos os dois, para não quebrar.
OAUTH_REDIRECT_URI = (
    os.getenv("OAUTH_REDIRECT_URI", "").strip()
    or os.getenv("FACEBOOK_REDIRECT_URI", "").strip()
    or "https://tec9-marketing-bot.onrender.com/auth/callback"
)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "").strip()

# Scopes configuráveis via env (para não dar "Invalid Scopes")
# Default seguro (quase sempre funciona):
DEFAULT_SCOPE = "pages_show_list,pages_manage_metadata"
OAUTH_SCOPE = os.getenv("OAUTH_SCOPE", DEFAULT_SCOPE).strip()

# Armazenamento simples (para testes)
AUTH_STORE = {
    "authenticated": False,
    "access_token": None,
    "token_data": None,
}

# ---------------- HEALTH ----------------
@app.get("/")
def home():
    return "Tec bot rodando no Render ✅", 200

@app.get("/health")
def health():
    return jsonify(status="ok"), 200

@app.get("/status")
def status():
    return jsonify(service="tec9-marketing-bot", up=True), 200


# ---------------- DIAGNÓSTICO ----------------
@app.get("/auth/debug")
def auth_debug():
    """
    Mostra quais variáveis estão chegando (sem revelar segredos).
    Use isso para conferir se o Render realmente aplicou as env vars.
    """
    return jsonify(
        ok=True,
        env={
            "FACEBOOK_APP_ID_present": bool(FACEBOOK_APP_ID),
            "FACEBOOK_APP_SECRET_present": bool(FACEBOOK_APP_SECRET),
            "OAUTH_REDIRECT_URI": OAUTH_REDIRECT_URI,
            "VERIFY_TOKEN_present": bool(VERIFY_TOKEN),
            "OAUTH_SCOPE": OAUTH_SCOPE,
        }
    ), 200


# ---------------- OAUTH ----------------
@app.get("/auth/facebook")
def auth_facebook():
    # Validação de ENV
    missing = []
    if not FACEBOOK_APP_ID:
        missing.append("FACEBOOK_APP_ID")
    if not FACEBOOK_APP_SECRET:
        missing.append("FACEBOOK_APP_SECRET")
    if not OAUTH_REDIRECT_URI:
        missing.append("OAUTH_REDIRECT_URI (ou FACEBOOK_REDIRECT_URI)")

    if missing:
        return jsonify(
            ok=False,
            error="Missing OAuth env vars",
            missing=missing,
            hint="Configure as ENV no Render e salve com 'Save, rebuild and deploy'."
        ), 500

    # Facebook aceita scope com vírgula, mas vamos normalizar e evitar espaços ruins
    # Ex: "pages_show_list,pages_manage_metadata"
    scope = ",".join([s.strip() for s in OAUTH_SCOPE.split(",") if s.strip()])

    params = {
        "client_id": FACEBOOK_APP_ID,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": scope,
        "state": "tec9"
    }

    url = "https://www.facebook.com/v19.0/dialog/oauth?" + urllib.parse.urlencode(params)
    return redirect(url)


@app.get("/auth/callback")
def auth_callback():
    # Se vier erro do Facebook
    fb_error = request.args.get("error")
    if fb_error:
        return jsonify(ok=False, error=fb_error, details=request.args.to_dict()), 400

    code = request.args.get("code")
    if not code:
        return jsonify(ok=False, error="Callback sem code", details=request.args.to_dict()), 400

    # Troca code por access_token
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    token_params = {
        "client_id": FACEBOOK_APP_ID,
        "client_secret": FACEBOOK_APP_SECRET,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "code": code
    }

    try:
        r = requests.get(token_url, params=token_params, timeout=30)
    except requests.RequestException as e:
        return jsonify(ok=False, error="Token exchange request failed", details=str(e)), 500

    if r.status_code != 200:
        return jsonify(ok=False, error="Token exchange failed", status=r.status_code, body=r.text), 500

    data = r.json()
    access_token = data.get("access_token")
    if not access_token:
        return jsonify(ok=False, error="No access_token in response", body=data), 500

    AUTH_STORE["authenticated"] = True
    AUTH_STORE["access_token"] = access_token
    AUTH_STORE["token_data"] = data

    return jsonify(ok=True, authenticated=True, token_received=True), 200


@app.get("/auth/status")
def auth_status():
    return jsonify(
        ok=True,
        authenticated=AUTH_STORE["authenticated"],
        has_token=bool(AUTH_STORE["access_token"])
    ), 200


# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200

        return "Forbidden", 403

    # POST (eventos)
    return jsonify(ok=True), 200
