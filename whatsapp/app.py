import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# ===== CONFIGURAÇÃO (Preencha ou use Variáveis de Ambiente) =====
# Dica: No servidor (Render/Railway), configure estas chaves nas 'Environment Variables'
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "sua_senha_escolhida_aqui")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "1099079283287430")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ===== ROTA DE TESTE =====
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀 - WhatsApp API operando", 200

# ===== VERIFICAÇÃO DO WEBHOOK (Obrigatório para o Meta) =====
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return challenge, 200
    return "Erro de verificação", 403

# ===== RECEBER E PROCESSAR MENSAGENS =====
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        # Verifica se é uma mensagem do WhatsApp
        if data.get("object") == "whatsapp_business_account":
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]

            if "messages" in value:
                message = value["messages"][0]
                from_number = message["from"]
                
                # Verifica se a mensagem é do tipo texto
                if message["type"] == "text":
                    text_body = message["text"]["body"]
                    print(f"Mensagem de {from_number}: {text_body}")

                    # 1. Gera resposta com a IA
                    resposta_ia = gerar_resposta(text_body)

                    # 2. Envia para o WhatsApp do cliente
                    enviar_mensagem(from_number, resposta_ia)

    except Exception as e:
        print(f"Erro no processamento: {e}")

    return "EVENT_RECEIVED", 200

# ===== INTEGRAÇÃO COM OPENAI =====
def gerar_resposta(pergunta):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini", # Nome corrigido
            messages=[
                {"role": "system", "content": "Você é um vendedor especialista da TEC9 informática. Seja profissional, objetivo, educado e focado em converter a conversa em venda."},
                {"role": "user", "content": pergunta}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Erro na OpenAI: {e}")
        return "Desculpe, tive um pequeno problema técnico. Pode repetir sua pergunta?"

# ===== ENVIO DE MENSAGEM VIA META API =====
def enviar_mensagem(numero, texto):
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": numero,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": texto
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status do envio: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
        return None

# ===== INICIALIZAÇÃO =====
if __name__ == "__main__":
    # O Railway/Render usam a variável PORT automaticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
