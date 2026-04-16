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

# ================================
# ROTAS DE TESTE E SAÚDE
# ================================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "online"}), 200

# ================================
# WEBHOOK: VERIFICAÇÃO (GET)
# ================================
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Token Inválido", 403

# ================================
# WEBHOOK: RECEBER MENSAGENS (POST)
# ================================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        # Verifica se o evento é uma mensagem válida do WhatsApp
        if data.get("entry") and data["entry"][0].get("changes"):
            value = data["entry"][0]["changes"][0]["value"]
            
            if "messages" in value:
                message = value["messages"][0]
                from_number = message["from"]
                
                if "text" in message:
                    user_text = message["text"]["body"]
                    print(f"Mensagem de {from_number}: {user_text}")

                    # 1. Gera a resposta com a IA
                    resposta_ia = gerar_resposta(user_text)

                    # 2. Envia de volta para o cliente
                    enviar_mensagem_whatsapp(from_number, resposta_ia)

    except Exception as e:
        print(f"Erro no processamento: {e}")

    return jsonify({"status": "ok"}), 200

# ================================
# FUNÇÃO: IA (OPENAI)
# ================================
def gerar_resposta(texto_usuario):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-4o-mini", # Modelo rápido e barato
            messages=[
                {"role": "system", "content": "Você é um vendedor especialista da TEC9 informática. Seja profissional e objetivo."},
                {"role": "user", "content": texto_usuario}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Erro OpenAI: {e}")
        return "Olá! Como posso ajudar você hoje?"

# ================================
# FUNÇÃO: ENVIAR WHATSAPP (META API)
# ================================
def enviar_mensagem_whatsapp(numero, texto):
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
        print(f"Envio para {numero}: {response.status_code}")
    except Exception as e:
        print(f"Erro ao enviar: {e}")

# ================================
# INICIALIZAÇÃO
# ================================
if __name__ == "__main__":
    # Garante que o app use a porta do Railway ou a 8080 por padrão
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
