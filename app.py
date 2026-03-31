from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 🔐 Variáveis do Railway
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# =========================
# 🔹 VERIFICAÇÃO WEBHOOK (META)
# =========================
@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Token inválido", 403


# =========================
# 🔹 RECEBER MENSAGENS
# =========================
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    print("📩 WEBHOOK RECEBIDO:", data)

    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']

        if 'messages' in value:
            message = value['messages'][0]
            from_number = message['from']

            if 'text' in message:
                text = message['text']['body']
                print(f"Mensagem recebida: {text}")

                # 🔥 RESPOSTA AUTOMÁTICA
                resposta = f"Olá! 👋\n\nRecebi sua mensagem:\n👉 {text}\n\nEm breve um especialista TEC9 vai te atender 🚀"
                
                send_message(from_number, resposta)

    except Exception as e:
        print("❌ ERRO:", e)

    return "ok", 200


# =========================
# 🔹 ENVIAR MENSAGEM WHATSAPP
# =========================
def send_message(to, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": text
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    print("📤 RESPOSTA ENVIADA:", response.status_code, response.text)


# =========================
# 🔹 ROTA TESTE (IMPORTANTE)
# =========================
@app.route('/')
def home():
    return "🚀 TEC9 BOT ONLINE"


# =========================
# 🔹 START (Railway)
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
