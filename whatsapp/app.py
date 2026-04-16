import os
import requests
from flask import Flask, request

app = Flask(__name__)

# ==============================
# VARIÁVEIS
# ==============================

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ==============================
# ROTAS DE TESTE (IMPORTANTES)
# ==============================

@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# ==============================
# WEBHOOK VERIFICATION
# ==============================

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Erro", 403

# ==============================
# RECEBER MENSAGEM
# ==============================

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        if data.get("entry"):
            for entry in data["entry"]:
                for change in entry["changes"]:
                    value = change.get("value", {})

                    if "messages" in value:
                        msg = value["messages"][0]
                        numero = msg["from"]

                        # evita loop
                        if msg.get("text"):
                            texto = msg["text"]["body"]

                            resposta = gerar_resposta(texto)
                            enviar_mensagem(numero, resposta)

    except Exception as e:
        print("ERRO:", e)

    return "ok", 200

# ==============================
# OPENAI
# ==============================

def gerar_resposta(texto):
    try:
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Você é um vendedor da TEC9 Informática."},
                {"role": "user", "content": texto}
            ]
        }

        r = requests.post(url, headers=headers, json=body)

        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]

        print("Erro OpenAI:", r.text)
        return "Erro ao gerar resposta."

    except Exception as e:
        print("Erro OpenAI:", e)
        return "Erro interno."

# ==============================
# ENVIO WHATSAPP
# ==============================

def enviar_mensagem(numero, mensagem):
    try:
        url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

        headers = {
            "Authorization": f"Bearer {META_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        body = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "text",
            "text": {"body": mensagem}
        }

        r = requests.post(url, headers=headers, json=body)

        print("ENVIO:", r.status_code, r.text)

    except Exception as e:
        print("Erro envio:", e)

# ==============================
# START (OBRIGATÓRIO RAILWAY)
# ==============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
