import os
import logging
from flask import Flask, request, jsonify

# ---------------------------------------
# LOGGING
# ---------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tec9-webhook")

# ---------------------------------------
# APP
# ---------------------------------------
app = Flask(__name__)

# ---------------------------------------
# CONFIG (Render ENV)
# ---------------------------------------
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "").strip()
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "").strip()

OAUTH_REDIRECT_URI = (
    os.getenv("OAUTH_REDIRECT_URI", "").strip()
    or os.getenv("FACEBOOK_REDIRECT_URI", "").strip()
    or "https://tec9-marketing-bot.onrender.com/auth/callback"
)

# ✅ IMPORTANTÍSSIMO: aceita os dois nomes no Render
VERIFY_TOKEN = (
    os.getenv("VERIFY_TOKEN", "").strip()
    or os.getenv("META_VERIFY_TOKEN", "").strip()
).strip()

DEFAULT_SCOPE = "pages_show_list,pages_manage_metadata"
OAUTH_SCOPE = os.getenv("OAUTH_SCOPE", DEFAULT_SCOPE).strip()

# ---------------------------------------
# HEALTH
# ---------------------------------------
@app.get("/")
def home():
    return "Tec9 bot rodando no Render ✅", 200

@app.get("/health")
def health():
    return jsonify(status="ok"), 200

# ---------------------------------------
# DEBUG (confere env sem mostrar segredos)
# ---------------------------------------
@app.get("/auth/debug")
def auth_debug():
    return jsonify(
        ok=True,
        env={
            "FACEBOOK_APP_ID_present": bool(FACEBOOK_APP_ID),
            "FACEBOOK_APP_SECRET_present": bool(FACEBOOK_APP_SECRET),
            "OAUTH_REDIRECT_URI": OAUTH_REDIRECT_URI,
            "OAUTH_SCOPE": OAUTH_SCOPE,
            "VERIFY_TOKEN_present": bool(VERIFY_TOKEN),
        },
    ), 200

# ---------------------------------------
# WEBHOOK META
# ---------------------------------------
@app.get("/webhook")
def webhook_verify():
    """
    Meta Webhook Verification:
    GET /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
    """
    mode = request.args.get("hub.mode", "")
    token = request.args.get("hub.verify_token", "")
    challenge = request.args.get("hub.challenge", "")

    logger.info(f"[WEBHOOK_VERIFY] mode={mode} token_len={len(token)} verify_present={bool(VERIFY_TOKEN)}")

    if mode == "subscribe" and VERIFY_TOKEN and token == VERIFY_TOKEN:
        logger.info("[WEBHOOK_VERIFY] ✅ Verified successfully")
        return challenge, 200

    logger.warning("[WEBHOOK_VERIFY] ❌ Verification failed")
    return "Forbidden", 403

@app.post("/webhook")
def webhook_receive():
    """
    Recebe eventos do webhook (Instagram/Facebook etc).
    Meta espera 200 rápido.
    """
    try:
        payload = request.get_json(silent=True) or {}
        logger.info(f"[WEBHOOK_EVENT] keys={list(payload.keys())[:10]}")
        return "EVENT_RECEIVED", 200
    except Exception as e:
        logger.exception(f"[WEBHOOK_EVENT] error={e}")
        return "ERROR", 200


# ---------------------------------------
# Local run (opcional)
# ---------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
