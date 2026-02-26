import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "tec9_verify_2026")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

@app.get("/")
def home():
    return "TEC9 bot rodando no Render ✅", 200

@app.get("/health")
def health():
    return jsonify(status="ok"), 200


# =========================
# 1) Verificação do Webhook
# =========================
@app.get("/webhook")
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado com sucesso")
        return challenge, 200

    print("❌ Webhook verify falhou:", {"mode": mode, "token_recebido": token})
    return "Token de verificação inválido", 403


# =========================
# 2) Receber Eventos IG
# =========================
@app.post("/webhook")
def receive():
    data = request.get_json(silent=True) or {}
    print("📩 EVENTO RECEBIDO:", data)

    try:
        # Estrutura padrão: entry -> messaging[]
        for entry in data.get("entry", []):
            for msg in entry.get("messaging", []):

                # Ignora eventos que não são mensagem de texto (read/delivery etc.)
                message_obj = msg.get("message")
                if not message_obj:
                    continue

                text = message_obj.get("text")
                if not text:
                    continue

                sender_id = msg.get("sender", {}).get("id")
                if not sender_id:
                    continue

                print("✅ Mensagem recebida:", text, "| sender_id:", sender_id)

                # Responder
                send_reply(sender_id)

    except Exception as e:
        print("🔥 ERRO no receive():", str(e))

    return "ok", 200


# =========================
# 3) Enviar Resposta
# =========================
def send_reply(user_id: str):
    if not ACCESS_TOKEN:
        print("❌ META_ACCESS_TOKEN NÃO definido no Render (Environment).")
        return

    url = "https://graph.facebook.com/v19.0/me/messages"

    payload = {
        "recipient": {"id": user_id},
        "message": {"text": "Olá 👋 Seja bem-vindo(a) à TEC9 Informática! Como posso ajudar você hoje?"}
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        print("📤 RESPOSTA ENVIADA:", r.status_code, r.text)
    except Exception as e:
        print("🔥 ERRO ao enviar resposta:", str(e))
