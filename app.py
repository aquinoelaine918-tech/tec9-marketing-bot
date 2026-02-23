import os
import urllib.parse
import requests
from flask import Flask, request, jsonify, redirect

app = Flask(__name__)

@app.get("/")
def home():
    return "Tec bot rodando no Render ✅", 200

@app.get("/health")
def health():
    return jsonify(status="ok"), 200

@app.get("/status")
def status():
    return jsonify(service="tec9-marketing-bot", up=True), 200

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

    return jsonify(received=True), 200

# LOGIN FACEBOOK
@app.get("/auth/facebook")
def auth_facebook():
    start = request.args.get("start")
    if start != "true":
        return jsonify(ok=True, message="Auth endpoint ativo"), 200

    app_id = os.getenv("FACEBOOK_APP_ID")
    redirect_uri = "https://tec9-marketing-bot.onrender.com/auth/callback"

    scope = "public_profile,email"

    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
    }

    url = "https://www.facebook.com/v19.0/dialog/oauth?" + urllib.parse.urlencode(params)
    return redirect(url)

# CALLBACK + TOKEN
@app.get("/auth/callback")
def auth_callback():
    code = request.args.get("code")

    if not code:
        return jsonify(ok=False, error="Callback sem code"), 400

    app_id = os.getenv("FACEBOOK_APP_ID")
    app_secret = os.getenv("FACEBOOK_APP_SECRET")
    redirect_uri = "https://tec9-marketing-bot.onrender.com/auth/callback"

    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"

    params = {
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }

    r = requests.get(token_url, params=params)
    data = r.json()

    return jsonify(
        ok=True,
        message="ACCESS TOKEN GERADO",
        token_response=data
    ), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
