import os
import json
import logging
import requests
from flask import Flask, request, jsonify

# =========================
# CONFIG LOG
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

app = Flask(__name__)

# =========================
# VARIÁVEIS DE AMBIENTE
# =========================
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "1142998738889284")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# =========================
# FUNÇÃO ENVIAR WHATSAPP
# =========================
def send_whatsapp(to, message):
    if not META_ACCESS_TOKEN or not PHONE_NUMBER_ID:
        logging.error("Credenciais da Meta não configuradas.")
        return

    # CORRIGIDO: URL completa da API da Meta
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        logging.info(f"Resposta Meta: {response.status_code} - {response.text}")
        return response.json()
    except Exception as e:
        logging.error(f"Erro ao enviar WhatsApp: {e}")
        return None

# =========================
# OPENAI (IA)
# =========================
def ask_openai(user_message):
    if not OPENAI_API_KEY:
        return ""

    # CORRIGIDO: URL completa da API da OpenAI
    url = "https://openai.com"
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Você é Iris, atendente da TEC9 Informática. Seja educada e objetiva. Foque em coletar modelo e quantidade para vendas/orçamentos."
            },
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Erro OpenAI: {e}")
        return ""

# =========================
# MENU PADRÃO
# =========================
def menu():
    return (
        "👋 Olá! Bem-vindo à TEC9 Informática.\n\n"
        "Escolha uma opção:\n"
        "1 - Vendas\n"
        "2 - Orçamento\n"
        "3 - Especialista\n\n"
        "Ou digite o produto que você procura."
    )

# =========================
# WEBHOOK GET (VERIFICAÇÃO)
# =========================
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logging.info("Webhook validado com sucesso!")
        return challenge, 200

    logging.warning("Falha na validação do Webhook. Verifique o VERIFY_TOKEN.")
    return "Token de verificação inválido", 403

# =========================
# WEBHOOK POST (RECEBE MSG)
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        # Extração corrigida para garantir que os índices existem
        if not data.get("entry") or not data["entry"][0].get("changes"):
            return "ok", 200
        
        value = data["entry"][0]["changes"][0].get("value", {})
        
        if "messages" not in value:
            return "ok", 200

        message = value["messages"][0]
        user_number = message["from"]

        if message.get("type") != "text":
            send_whatsapp(user_number, menu())
            return "ok", 200

        user_text = message["text"]["body"].lower().strip()

        # Lógica de Menu
        if user_text in ["oi", "olá", "ola", "menu", "bom dia", "boa tarde"]:
            send_whatsapp(user_number, menu())
        elif user_text == "1":
            send_whatsapp(user_number, "💻 Perfeito! Qual produto ou modelo você procura?")
        elif user_text == "2":
            send_whatsapp(user_number, "📄 Para orçamento envie:\n• Produto\n• Quantidade\n• Email\n• CNPJ (se empresa)")
        elif user_text == "3":
            send_whatsapp(user_number, "👨‍💼 Vou te direcionar a um especialista. Me diga qual sua necessidade.")
        else:
            ai_response = ask_openai(user_text)
            if ai_response:
                send_whatsapp(user_number, ai_response)
            else:
                send_whatsapp(user_number, "Recebi sua mensagem! Informe o modelo do produto ou escolha uma opção do menu (1, 2 ou 3).")

    except Exception as e:
        logging.error(f"Erro no processamento: {e}")

    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "BOT TEC9 ONLINE", 200

# =========================
# EXECUÇÃO
# =========================
if __name__ == "__main__":
    # Garante que o Flask use a porta fornecida pelo Railway
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
