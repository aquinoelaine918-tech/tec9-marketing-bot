import os
from flask import request

VERIFY_TOKEN = (os.getenv("META_VERIFY_TOKEN") or os.getenv("VERIFY_TOKEN") or "").strip()

@app.get("/webhook")
def verify():
    try:
        mode = request.args.get("hub.mode", "")
        token = request.args.get("hub.verify_token", "")
        challenge = request.args.get("hub.challenge", "")

        print("DEBUG TOKEN RECEBIDO:", token)
        print("DEBUG TOKEN ESPERADO:", VERIFY_TOKEN)

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200

        return "Token de verificação inválido", 403

    except Exception as e:
        print("ERRO NO WEBHOOK:", e)
        return "Erro interno", 500
