import os
import json
import logging
from typing import Any, Dict, Optional

import requests
from flask import Flask, request, jsonify

# =========================
# CONFIGURAÇÃO DE LOG
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

app = Flask(__name__)

# =========================
# VARIÁVEIS DE AMBIENTE
# =========================
# Certifique-se de configurar estas variáveis no seu painel de hospedagem
VERIFY_TOKEN = os.getenv("tec9token123", "")
META_ACCESS_TOKEN = os.getenv("EAAK409sUM3YBRFbeMaGZCmqKwvwaRnkQW3ZCpco9zNr0SkfhvYa71LP5mqroU0gn9tS6M5Mx9CO9DTj4idPSysCZA6aKDw3ZBkWlitlzKEAmIOBOI0l2MscoodRn7FLVHlKqW3UjhZCqvA8XIs2iRi23TTL6t5uZC65VD59zf1ePJdT3hwLh3baKm2J9JON0VynQZDZD", "")
PHONE_NUMBER_ID = os.getenv("1142998738889284", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Corrigido para o modelo oficial atual
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# =========================
# VALIDAÇÕES INICIAIS
# =========================
if not VERIFY_TOKEN:
    logging.warning("VERIFY_TOKEN não configurado.")
if not META_ACCESS_TOKEN:
    logging.warning("META_ACCESS_TOKEN não configurado.")
if not PHONE_NUMBER_ID:
    logging.warning("PHONE_NUMBER_ID não configurado.")

# Memória temporária (Reinicia se o servidor desligar)
user_state: Dict[str, Dict[str, Any]] = {}

# =========================
# FUNÇÕES AUXILIARES
# =========================
def get_menu_text() -> str:
    return (
        "Olá! Seja bem-vindo à TEC9 Informática.\n\n"
        "Escolha uma opção:\n"
        "1 - Vendas\n"
        "2 - Orçamento\n"
        "3 - Especialista TEC9\n\n"
        "Se preferir, você também pode digitar diretamente o produto ou modelo que procura."
    )

def normalize_text(text: str) -> str:
    return (text or "").strip().lower()

def send_whatsapp_text(to_number: str, message_text: str) -> Dict[str, Any]:
    if not META_ACCESS_TOKEN or not PHONE_NUMBER_ID:
        raise RuntimeError("Configurações da Meta ausentes.")

    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"preview_url": False, "body": message_text}
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    return response.json()

def extract_text_message(data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    try:
        value = data["entry"][0]["changes"][0]["value"]
        if "messages" not in value:
            return None

        message = value["messages"][0]
        contact = value.get("contacts", [{}])[0]

        return {
            "from": message.get("from", ""),
            "name": contact.get("profile", {}).get("name", "Cliente"),
            "text": message.get("text", {}).get("body", "") if message.get("type") == "text" else ""
        }
    except Exception:
        return None

def ask_openai(user_number: str, user_name: str, user_message: str) -> str:
    if not OPENAI_API_KEY:
        return ""

    system_prompt = (
        "Você é Iris, atendente da TEC9 Informática no WhatsApp. "
        "Responda de forma profissional e cordial. "
        "Se o cliente quiser comprar ou orçamento, peça modelo e quantidade. "
        "Não invente preços ou estoques."
    )

    url = "https://openai.com"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Cliente: {user_name} ({user_number})\nMsg: {user_message}"}
        ],
        "temperature": 0.7
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        return res.json()["choices"][0]["message"]["content"].strip()
    except:
        return ""

def build_local_response(user_number: str, user_message: str) -> str:
    text = normalize_text(user_message)
    
    if text in ["1", "vendas"]:
        return "Ótimo! Qual produto ou modelo você procura?"
    if text in ["2", "orçamento", "orcamento"]:
        return "Para orçamentos, informe: Nome, Produto, Quantidade e E-mail."
    if text in ["3", "especialista"]:
        return "Vou te conectar a um especialista. Um momento."
    
    return get_menu_text()

# =========================
# ROTAS DO FLASK
# =========================
@app.route("/", methods=["GET"])
def index():
    return "TEC9 Bot Online", 200

@app.route("/webhook", methods=["GET"])
def verify():
    # Validação exigida pela Meta para ativar o Webhook
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Token Inválido", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    msg_data = extract_text_message(data)

    if msg_data and msg_data["text"]:
        user_num = msg_data["from"]
        user_name = msg_data["name"]
        user_msg = msg_data["text"]

        # Tenta OpenAI, se falhar usa o menu local
        reply = ask_openai(user_num, user_name, user_msg)
        if not reply:
            reply = build_local_response(user_num, user_msg)

        send_whatsapp_text(user_num, reply)

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
