import os
import requests
from flask import Flask, request, jsonify

# ==============================
# CONFIGURAÇÕES
# ==============================

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# ==============================
# ROTA TESTE
# ==============================

@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# ==============================
# VERIFICAÇÃO WEBHOOK (META)
# ==============================

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Erro de verificação", 403

# ==============================
# RECEBER MENSAGEM WHATSAPP
# ==============================

@app.route("/webhook", methods=["POST"])
def receber_mensagem():
    data = request.get_json()

    try:
        if "entry" in data:
            for entry in data["entry"]:
                for change in entry["changes"]:
                    if "value" in change and "messages" in change["value"]:
                        mensagem = change["value"]["messages"][0]
                        numero = mensagem["from"]

                        # evita loop de mensagens da própria API
                        if mensagem.get("id"):
                            texto = mensagem["text"]["body"]

                            resposta = gerar_resposta(texto)
                            enviar_mensagem(numero, resposta)

    except Exception as e:
        print("Erro ao processar mensagem:", e)

    return "ok", 200

# ==============================
# GERAR RESPOSTA COM OPENAI
# ==============================

def gerar_resposta(texto_usuario):
    try:
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Você é um vendedor profissional da TEC9 Informática."},
                {"role": "user", "content": texto_usuario}
            ]
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            resposta = response.json()
            return resposta["choices"][0]["message"]["content"]
        else:
            print("Erro OpenAI:", response.text)
            return "Desculpe, ocorreu um erro ao gerar resposta."

    except Exception as e:
        print("Erro OpenAI Exception:", e)
        return "Erro interno ao processar mensagem."

# ==============================
# ENVIAR MENSAGEM WHATSAPP
# ==============================

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
        "text": {"body": mensagem}
    }

    response = requests.post(url, headers=headers, json=payload)

    print("STATUS:", response.status_code)
    print("RESPOSTA:", response.text)

# ==============================
# INICIALIZAÇÃO (RAILWAY)
# ==============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
