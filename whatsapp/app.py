import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Configurações básicas
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "123456")

@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# WEBHOOK PARA O FACEBOOK VALIDAR
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Token Inválido", 403

# RECEBER MENSAGENS E RESPONDER
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        if data.get("entry"):
            changes = data["entry"][0].get("changes")[0]["value"]
            if "messages" in changes:
                msg = changes["messages"][0]
                numero = msg["from"]
                texto_usuario = msg["text"]["body"]

                # Chama a IA e envia a resposta
                resposta = gerar_resposta(texto_usuario)
                enviar_whatsapp(numero, resposta)
    except:
        pass
    return "OK", 200

def gerar_resposta(pergunta):
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um vendedor da TEC9 informática."},
                {"role": "user", "content": pergunta}
            ]
        )
        return res.choices[0].message.content
    except:
        return "Olá! Como posso ajudar você hoje?"

def enviar_whatsapp(numero, texto):
    url = f"https://facebook.com{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {"Authorization": f"Bearer {os.getenv('META_ACCESS_TOKEN')}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": numero, "type": "text", "text": {"body": texto}}
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
