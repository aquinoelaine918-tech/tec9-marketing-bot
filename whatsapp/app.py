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
VERIFY_TOKEN = os.getenv("tec9token123", "")
META_ACCESS_TOKEN = os.getenv("EAAK409sUM3YBRFbeMaGZCmqKwvwaRnkQW3ZCpco9zNr0SkfhvYa71LP5mqroU0gn9tS6M5Mx9CO9DTj4idPSysCZA6aKDw3ZBkWlitlzKEAmIOBOI0l2MscoodRn7FLVHlKqW3UjhZCqvA8XIs2iRi23TTL6t5uZC65VD59zf1ePJdT3hwLh3baKm2J9JON0VynQZDZD", "")
PHONE_NUMBER_ID = os.getenv("1142998738889284", "")
OPENAI_API_KEY = os.getenv ("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# =========================
# VALIDAÇÕES INICIAIS
# =========================
if not VERIFY_TOKEN:
    logging.warning("VERIFY_TOKEN não configurado.")
if not META_ACCESS_TOKEN:
    logging.warning("META_ACCESS_TOKEN não configurado.")
if not PHONE_NUMBER_ID:
    logging.warning("PHONE_NUMBER_ID não configurado.")

# =========================
# MEMÓRIA SIMPLES EM RAM
# =========================
# Para produção avançada, o ideal é usar banco de dados.
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
    """
    Envia mensagem de texto via WhatsApp Cloud API.
    """
    if not META_ACCESS_TOKEN or not PHONE_NUMBER_ID:
        raise RuntimeError("META_ACCESS_TOKEN ou PHONE_NUMBER_ID não configurado.")

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message_text
        }
    }

    logging.info("Enviando mensagem para %s", to_number)
    response = requests.post(url, headers=headers, json=payload, timeout=30)

    try:
        response_json = response.json()
    except Exception:
        response_json = {"raw_response": response.text}

    if response.status_code >= 400:
        logging.error("Erro ao enviar mensagem: %s", response_json)
        raise RuntimeError(f"Erro Meta API: {response_json}")

    logging.info("Mensagem enviada com sucesso: %s", response_json)
    return response_json


def extract_text_message(data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Extrai número e texto da mensagem recebida.
    Retorna:
    {
        "from": "5511999999999",
        "name": "Nome",
        "text": "mensagem"
    }
    """
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Ignora status de entrega/leitura
        if "messages" not in value:
            return None

        message = value["messages"][0]
        contact = value.get("contacts", [{}])[0]

        msg_type = message.get("type")

        if msg_type != "text":
            return {
                "from": message.get("from", ""),
                "name": contact.get("profile", {}).get("name", "Cliente"),
                "text": ""
            }

        return {
            "from": message.get("from", ""),
            "name": contact.get("profile", {}).get("name", "Cliente"),
            "text": message.get("text", {}).get("body", "")
        }

    except Exception as e:
        logging.exception("Erro ao extrair mensagem: %s", e)
        return None


def ask_openai(user_number: str, user_name: str, user_message: str) -> str:
    """
    Integração simples com OpenAI via REST.
    Se não houver chave, retorna string vazia.
    """
    if not OPENAI_API_KEY:
        return ""

    system_prompt = (
        "Você é Iris, atendente comercial da TEC9 Informática no WhatsApp. "
        "Responda em português do Brasil, com tom profissional, objetivo e cordial. "
        "Seu papel é ajudar em vendas, orçamento e direcionamento comercial. "
        "Se o cliente pedir preço, prazo, estoque, entrega ou pagamento, conduza a conversa de forma comercial. "
        "Se a conversa pedir orçamento empresarial, solicite nome da empresa, CNPJ, e-mail e quantidade. "
        "Se o cliente estiver indeciso, peça produto/modelo, quantidade e cidade/CEP. "
        "Evite respostas longas. Não invente estoque nem prazo exato. "
        "Sempre mantenha um tom de atendimento comercial profissional."
    )

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Nome do cliente: {user_name}\n"
                    f"Número: {user_number}\n"
                    f"Mensagem: {user_message}"
                )
            }
        ],
        "temperature": 0.5,
        "max_tokens": 300
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        result = response.json()

        if response.status_code >= 400:
            logging.error("Erro OpenAI: %s", result)
            return ""

        content = result["choices"][0]["message"]["content"].strip()
        return content

    except Exception as e:
        logging.exception("Erro ao consultar OpenAI: %s", e)
        return ""


def build_local_response(user_number: str, user_name: str, user_message: str) -> str:
    """
    Fluxo local simples caso a OpenAI não esteja configurada.
    """
    text = normalize_text(user_message)

    # Primeira interação
    if user_number not in user_state:
        user_state[user_number] = {"started": True}
        if text in {"oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", ""}:
            return get_menu_text()

    # Menu
    if text == "1":
        return (
            "Perfeito! Você escolheu *Vendas*.\n\n"
            "Me informe o produto ou modelo que você procura.\n"
            "Se quiser, pode enviar também a quantidade desejada e sua cidade ou CEP."
        )

    if text == "2":
        return (
            "Perfeito! Para *Orçamento*, me envie por favor:\n\n"
            "• Nome\n"
            "• Produto ou modelo\n"
            "• Quantidade\n"
            "• E-mail\n"
            "• CNPJ (se for empresa)\n\n"
            "Assim seguimos com mais agilidade."
        )

    if text == "3":
        return (
            "Claro! Vou te direcionar para um *Especialista TEC9*.\n\n"
            "Antes, me diga rapidamente qual produto ou necessidade você tem para agilizar o atendimento."
        )

    # Lead quente
    hot_keywords = [
        "preço", "preco", "valor", "quanto custa", "prazo",
        "entrega", "estoque", "pagamento", "pix"
    ]

    if any(keyword in text for keyword in hot_keywords):
        return (
            "Perfeito. Para eu te passar isso com mais precisão, me informe por favor:\n\n"
            "• Produto ou modelo exato\n"
            "• Quantidade desejada\n"
            "• Cidade ou CEP\n\n"
            "Assim seguimos com agilidade no atendimento."
        )

    # Saudação/menu
    if text in {"oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "menu"}:
        return get_menu_text()

    # Resposta padrão
    return (
        "Recebi sua mensagem. Para eu te ajudar melhor, me envie o produto ou modelo que você procura.\n\n"
        "Se preferir, digite:\n"
        "1 - Vendas\n"
        "2 - Orçamento\n"
        "3 - Especialista TEC9"
    )


# =========================
# ROTAS
# =========================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE", 200


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Verificação do webhook pela Meta.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    logging.info(
        "Webhook GET recebido | mode=%s | token_recebido=%s",
        mode, token
    )

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logging.info("Webhook verificado com sucesso!")
        return challenge, 200

    logging.warning("Token de verificação inválido.")
    return "Token de verificação inválido", 403


@app.route("/webhook", methods=["POST"])
def webhook_receiver():
    """
    Recebe mensagens da Meta e responde no WhatsApp.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        logging.info("Webhook POST recebido: %s", json.dumps(data, ensure_ascii=False))

        msg_data = extract_text_message(data)

        if not msg_data:
            logging.info("Evento ignorado: sem mensagem processável.")
            return jsonify({"status": "ignored"}), 200

        user_number = msg_data.get("from", "")
        user_name = msg_data.get("name", "Cliente")
        user_text = msg_data.get("text", "")

        if not user_number:
            logging.warning("Evento sem número do remetente.")
            return jsonify({"status": "ignored_no_number"}), 200

        logging.info(
            "Mensagem recebida | de=%s | nome=%s | texto=%s",
            user_number, user_name, user_text
        )

        # Tenta OpenAI primeiro
        reply_text = ""
        if OPENAI_API_KEY:
            try:
                reply_text = ask_openai(user_number, user_name, user_text)
            except Exception as e:
                logging.exception("Erro ao consultar OpenAI: %s", e)
                reply_text = ""

        # Se não houver resposta da OpenAI, usa fluxo local
        if not reply_text:
            reply_text = build_local_response(user_number, user_name, user_text)

        # Envia resposta
        send_result = send_whatsapp_text(user_number, reply_text)

        logging.info("Resposta enviada com sucesso: %s", send_result)
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logging.exception("Erro no webhook POST: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)
