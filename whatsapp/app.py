from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# =========================
# ROTAS DE TESTE
# =========================

@app.route("/")
def home():
    return "TEC9 BOT ONLINE 🚀", 200

@app.route("/health")
def health():
    return "OK", 200

# =========================
# VERIFICAÇÃO WEBHOOK
# =========================

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Erro de verificação", 403

# =========================
# RECEBER MENSAGENS
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        number = message["from"]
        text = message["text"]["body"]

        print("Mensagem recebida:", text)

        enviar_mensagem(number, f"Recebi: {text}")

    except Exception as e:
        print("Erro:", e)

    return "OK", 200

# =========================
# ENVIAR MENSAGEM
# =========================

def enviar_mensagem(numero, mensagem):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": mensagem
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("Resposta envio:", response.text)

# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
