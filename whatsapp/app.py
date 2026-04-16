import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# ===== CONFIG =====
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ===== TESTE =====
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀"

@app.route("/health", methods=["GET"])
def health():
    return "OK"

# ===== VERIFICAÇÃO DO WEBHOOK =====
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Erro de verificação", 403

# ===== RECEBER MENSAGEM =====
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]
            from_number = message["from"]
            text = message["text"]["body"]

            print(f"Mensagem recebida de {from_number}: {text}")

            # ===== RESPOSTA COM IA =====
            resposta = gerar_resposta(text)

            # ===== ENVIAR RESPOSTA =====
            enviar_mensagem(from_number, resposta)

    except Exception as e:
        print("Erro:", e)

    return "ok", 200

# ===== IA =====
def gerar_resposta(pergunta):
    try:
        resposta = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um vendedor especialista da TEC9 informática. Seja profissional, objetivo e ajude a vender."},
                {"role": "user", "content": pergunta}
            ]
        )
        return resposta.choices[0].message.content
    except Exception as e:
        print("Erro IA:", e)
        return "Desculpe, tive um problema. Pode repetir?"

# ===== ENVIO WHATSAPP =====
def enviar_mensagem(numero, texto):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": texto
        }
    }

    response = requests.post(url, headers=headers, json=data)
    print("Resposta envio:", response.text)

# ===== RODAR =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
