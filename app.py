import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIÁVEIS DO RENDER
# =========================
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")  # ID numérico da conta IG Business

# =========================
# TESTE ONLINE
# =========================
@app.get("/")
def home():
    return "TEC9 BOT ONLINE ✅", 200

@app.get("/health")
def health():
    return jsonify(status="ok"), 200

# =========================
# VERIFICAÇÃO META (WEBHOOK)
# =========================
@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado com sucesso!")
        return challenge, 200

    print("❌ Falha na verificação: Token inválido")
    return "erro", 403

# =========================
# RECEBE EVENTOS DO INSTAGRAM
# =========================
@app.post("/webhook")
def receive_webhook():
    data = request.get_json()
    
    if data.get("object") != "instagram":
        return "ok", 200

    try:
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                message = messaging.get("message", {})
                
                # 🛑 IMPORTANTE: Ignora mensagens enviadas pelo próprio bot (echo)
                if message.get("is_echo"):
                    return "ok", 200

                text = message.get("text")

                if sender_id and text:
                    print(f"📩 MENSAGEM RECEBIDA de {sender_id}: {text}")
                    
                    # Lógica de Resposta
                    reply = "Olá 👋 Seja bem-vindo(a) à TEC9 Informática! Como posso ajudar você hoje?"
                    send_message(sender_id, reply)

    except Exception as e:
        print("❌ ERRO AO PROCESSAR WEBHOOK:", str(e))

    return "ok", 200

# =========================
# ENVIO DE MENSAGEM (API GRAPH)
# =========================
def send_message(recipient_id, text):
    if not META_ACCESS_TOKEN or not IG_USER_ID:
        print("❌ ERRO: META_ACCESS_TOKEN ou IG_USER_ID não configurados no Render.")
        return

    # Usando v19.0 como no seu código original
    url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()
        
        if response.status_code == 200:
            print(f"📤 RESPOSTA ENVIADA com sucesso para {recipient_id}")
        else:
            print(f"❌ ERRO NA API META: {res_data}")
            
    except Exception as e:
        print("❌ ERRO DE CONEXÃO AO ENVIAR:", str(e))

if __name__ == "__main__":
    # O Render define a porta automaticamente na variável PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
