import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIÁVEIS DE AMBIENTE
# =========================
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "tec9_verify_2026")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")  # Token gerado no Meta (Instagram API Setup)
IG_USER_ID = os.environ.get("IG_USER_ID")  # ID numérico do Instagram (ex: 1784....)

# =========================
# ROTAS DE TESTE
# =========================
@app.get("/")
def home():
    return "Tec bot rodando no Render ✅", 200

@app.get("/health")
def health():
    return jsonify(status="ok"), 200

# =========================
# WEBHOOK - VERIFICAÇÃO META
# =========================
@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Token de verificação inválido", 403

# =========================
# WEBHOOK - RECEBE EVENTOS
# =========================
@app.post("/webhook")
def webhook_receive():
    data = request.get_json(silent=True) or {}
    print("EVENTO RECEBIDO:", data)

    # Eventos do Instagram vêm assim: object='instagram' e entry[]
    if data.get("object") != "instagram":
        return "ignored", 200

    try:
        for entry in data.get("entry", []):
            # Para IG Messaging API, os eventos costumam vir em entry.messaging[]
            for msg in entry.get("messaging", []):
                message = msg.get("message", {})
                sender = msg.get("sender", {})
                sender_id = sender.get("id")

                text = message.get("text", "")
                print(f"💬 Mensagem recebida de {sender_id}: {text}")

                # Só responde quando existe texto e remetente
                if sender_id and text:
                    reply_text = "Olá 👋 Seja bem-vindo(a) à TEC9 Informática! Como posso ajudar você hoje?"
                    send_instagram_message(sender_id, reply_text)

        return "ok", 200

    except Exception as e:
        print("❌ ERRO NO WEBHOOK:", str(e))
        return "error", 200


# =========================
# ENVIA MENSAGEM PARA INSTAGRAM
# =========================
def send_instagram_message(recipient_id: str, text: str):
    if not META_ACCESS_TOKEN:
        print("❌ META_ACCESS_TOKEN não definido no Render")
        return

    if not IG_USER_ID:
        print("❌ IG_USER_ID não definido no Render")
        print("➡️ Crie no Render: IG_USER_ID = (ID numérico do Instagram na tela do Meta)")
        return

    url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/messages"

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }

    params = {"access_token": META_ACCESS_TOKEN}

    try:
        resp = requests.post(url, json=payload, params=params, timeout=20)
        print("📤 RESPOSTA ENVIADA:", resp.status_code, resp.text)
    except Exception as e:
        print("❌ ERRO AO ENVIAR:", str(e))
