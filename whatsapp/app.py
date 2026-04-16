import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ================================
# CONFIGURAÇÕES
# ================================
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ================================
# ROTA PRINCIPAL (TESTE)
# ================================
@app.route("/", methods=["GET"])
def home():
    return "FUNCIONANDO TEC9 🚀", 200

# ================================
# HEALTH CHECK (IMPORTANTE)
# ================================
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# ================================
# WEBHOOK (VERIFICAÇÃO META)
# ================================
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Erro na verificação", 403

# ================================
# RECEBER MENSAGENS
# ================================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        print("📩 Mensagem recebida:", data)

        if data.get("entry"):
            for entry in data["entry"]:
                for change in entry["changes"]:
                    value = change["value"]

                    if "messages" in value:
                        message = value["messages"][0]
                        from_number = message["from"]

                        if "text" in message:
                            text = message["text"]["body"]

                            resposta = gerar_resposta(text)
                            enviar_mensagem(from_number, resposta)

        return "ok", 200

    except Exception as e:
        print("❌ ERRO:", str(e))
        return "erro", 500

# ================================
# GERAR RESPOSTA IA
# ================================
def gerar_resposta(texto):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um vendedor profissional da TEC9 Informática."},
                {"role": "user", "content": texto}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Erro OpenAI:", e)
        return "Olá! Recebi sua mensagem. Em breve um especialista vai te atender."

# ================================
# ENVIAR MENSAGEM WHATSAPP
# ================================
def enviar_mensagem(numero, texto):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

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

    print("📤 Envio:", response.text)

# ================================
# EXECUÇÃO LOCAL (RAILWAY USA GUNICORN)
# ================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
