import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# ================================
# CONFIGURAÇÕES (VARIÁVEIS DE AMBIENTE)
# ================================
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "123456")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializa o cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ================================
# ROTAS DE SAÚDE (PARA O RAILWAY)
# ================================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "working"}), 200

# ================================
# VERIFICAÇÃO DO WEBHOOK (META)
# ================================
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook validado com sucesso!")
        return challenge, 200
    
    return "Token de verificação inválido", 403

# ================================
# RECEBIMENTO DE MENSAGENS
# ================================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        # Verifica se é uma mensagem do WhatsApp
        if data.get("entry") and data["entry"][0].get("changes") and "messages" in data["entry"][0]["changes"][0]["value"]:
            
            value = data["entry"][0]["changes"][0]["value"]
            message = value["messages"][0]
            from_number = message["from"]

            # Processa apenas se for mensagem de texto
            if "text" in message:
                user_text = message["text"]["body"]
                print(f"Mensagem de {from_number}: {user_text}")

                # 1. Gera resposta com IA
                resposta_ia = gerar_resposta(user_text)

                # 2. Envia de volta para o WhatsApp
                enviar_mensagem(from_number, resposta_ia)

    except Exception as e:
        print(f"Erro ao processar webhook: {e}")

    return "OK", 200

# ================================
# FUNÇÃO DA IA (OPENAI)
# ================================
def gerar_resposta(pergunta):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini", # Modelo atualizado e estável
            messages=[
                {"role": "system", "content": "Você é um vendedor especialista da TEC9 informática. Seja profissional, objetivo e ajude a vender."},
                {"role": "user", "content": pergunta}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Erro OpenAI: {e}")
        return "Desculpe, tive um probleminha técnico. Pode repetir?"

# ================================
# FUNÇÃO DE ENVIO (META API)
# ================================
def enviar_mensagem(numero, texto):
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Envio: {response.status_code}")
    except Exception as e:
        print(f"Erro ao enviar: {e}")

# ================================
# EXECUÇÃO DO APP
# ================================
if __name__ == "__main__":
    # Importante: O Railway exige que a porta seja dinâmica
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
