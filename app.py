import os
import urllib.parse
import requests
from flask import Flask, request, jsonify, redirect

app = Flask(__name__)

# --- CONFIG ---
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "https://tec9-marketing-bot.onrender.com/auth/callback")

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "")

# Armazenamento simples (para funcionar já). Em produção ideal é banco/redis.
AUTH_STORE = {
    "authenticated": False,
    "access_token": None
}


@app.get("/")
def home():
    return "Tec bot rodando no Render ✅", 200


@app.get("/health")
def health():
    return jsonify(status="ok"), 200


@app.get("/status")
def status():
    return jsonify(service="tec9-marketing-bot", up=True), 200


# ---------------- OAUTH (REAL) ----------------
@app.get("/auth/facebook")
def auth_facebook():
    # Se faltar config, já mostra claro
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET or not OAUTH_REDIRECT_URI:
        return jsonify(
            ok=False,
            error="Missing OAuth env vars",
            FACEBOOK_APP_ID=bool(FACEBOOK_APP_ID),
            FACEBOOK_APP_SECRET=bool(FACEBOOK_APP_SECRET),
            OAUTH_REDIRECT_URI=OAUTH_REDIRECT_URI
        ), 500

    # Escopos: ajuste conforme o que seu app precisa
    scope = ",".join([
        "pages_show_list",
        "pages_manage_metadata",
        "pages_messaging",
        "instagram_basic",
        "instagram_manage_messages"
    ])

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
    error = request.args.get("error")
    if error:
        return jsonify(ok=False, error=error, details=request.args.to_dict()), 400

    code = request.args.get("code")
    if not code:
        return jsonify(ok=False, error="Missing code", details=request.args.to_dict()), 400

    # Trocar code por access_token
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    token_params = {
        "client_id": FACEBOOK_APP_ID,
        "client_secret": FACEBOOK_APP_SECRET,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "code": code
    }

    r = requests.get(token_url, params=token_params, timeout=30)
    if r.status_code != 200:
        return jsonify(ok=False, error="Token exchange failed", status=r.status_code, body=r.text), 500

    data = r.json()
    access_token = data.get("access_token")
    if not access_token:
        return jsonify(ok=False, error="No access_token in response", body=data), 500

    AUTH_STORE["authenticated"] = True
    AUTH_STORE["access_token"] = access_token

    return jsonify(ok=True, authenticated=True)


@app.get("/auth/status")
def auth_status():
    return jsonify(authenticated=AUTH_STORE["authenticated"], ok=True), 200


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
