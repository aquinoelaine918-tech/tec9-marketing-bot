import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIAVEIS DE AMBIENTE
# =========================
VERIFY_TOKEN = (os.getenv("VERIFY_TOKEN") or "").strip()
ACCESS_TOKEN = (os.getenv("META_ACCESS_TOKEN") or "").strip()
PHONE_NUMBER_ID = (os.getenv("PHONE_NUMBER_ID") or "").strip()

# =========================
# AGENTES
# =========================
AGENTE_VENDAS = "Camila"
AGENTE_SUPORTE = "Lucas"
AGENTE_ESPECIALISTA = "Ricardo"

# =========================
# PALAVRAS-CHAVE
# =========================
PALAVRAS_MENU = [
    "oi", "olá", "ola", "menu", "inicio", "início", "bom dia", "boa tarde", "boa noite"
]

PALAVRAS_CLIENTE_QUENTE = [
    "preco", "preço", "valor", "quanto custa", "orcamento", "orçamento",
    "prazo", "entrega", "estoque", "disponivel", "disponível", "frete",
    "pagamento", "pix", "boleto", "cartao", "cartão", "comprar",
    "cotacao", "cotação", "pedido", "urgente"
]

# =========================
# TEXTOS
# =========================
MENSAGEM_INICIAL = (
    "Olá! Seja bem-vindo(a) à *TEC9 Informática*.\n\n"
    "Você será atendido(a) por nossa equipe especializada:\n\n"
    f"1 - *{AGENTE_VENDAS}* | Orçamentos e Vendas\n"
    f"2 - *{AGENTE_SUPORTE}* | Suporte Técnico\n"
    f"3 - *{AGENTE_ESPECIALISTA}* | Especialista TEC9\n\n"
    "Digite apenas o número da opção desejada."
)

# 🔥 OPÇÃO 1 AGORA É VENDAS
MENSAGEM_VENDAS = (
    f"💰 *{AGENTE_VENDAS} | Consultora Comercial TEC9*\n\n"
    "Vou te ajudar com seu orçamento.\n\n"
    "Por favor, envie:\n\n"
    "- Nome\n"
    "- quantidade desejada\n"
    "- nome do produto ou modelo\n"
    "- email\n\n"
    "Se a compra for para empresa informe também o *CNPJ*.\n\n"
    "Assim conseguiremos encaminhar uma proposta mais precisa e rápida."
)

# 🔥 OPÇÃO 2 SUPORTE
MENSAGEM_SUPORTE = (
    f"🔧 *{AGENTE_SUPORTE} | Suporte Técnico TEC9*\n\n"
    "Vou dar sequência ao seu atendimento.\n\n"
    "Por favor, informe:\n"
    "- marca do equipamento\n"
    "- modelo do equipamento\n"
    "- qual a dúvida\n"
    "- defeito ou situação apresentada\n\n"
    "Nossa equipe técnica irá analisar sua solicitação."
)

# 🔥 OPÇÃO 3 ESPECIALISTA
MENSAGEM_ESPECIALISTA = (
    f"👤 *{AGENTE_ESPECIALISTA} | Especialista TEC9*\n\n"
    "Vou assumir seu atendimento a partir deste momento.\n\n"
    "Para agilizar, envie:\n"
    "- nome\n"
    "- produto ou necessidade\n"
    "- quantidade\n"
    "- email\n\n"
    "Se for empresa, informe também o *CNPJ*."
)

MENSAGEM_PRECO = (
    f"💰 *{AGENTE_VENDAS} | Comercial TEC9*\n\n"
    "Para verificar preço, envie:\n\n"
    "- Nome\n"
    "- quantidade desejada\n"
    "- produto ou modelo\n"
    "- email\n\n"
    "Se for empresa, informe também o *CNPJ*."
)

MENSAGEM_PRAZO = (
    f"🚚 *{AGENTE_VENDAS} | Comercial TEC9*\n\n"
    "Para validar prazo e entrega, envie:\n\n"
    "- produto\n"
    "- quantidade\n"
    "- email\n"
)

MENSAGEM_ESTOQUE = (
    f"📦 *{AGENTE_VENDAS} | Comercial TEC9*\n\n"
    "Para verificar estoque, envie:\n\n"
    "- produto\n"
    "- quantidade\n"
)

MENSAGEM_CLIENTE_QUENTE = (
    f"🔥 *{AGENTE_VENDAS} | Atendimento Prioritário*\n\n"
    "Vamos agilizar seu atendimento.\n\n"
    "Envie:\n"
    "- Nome\n"
    "- quantidade desejada\n"
    "- produto ou modelo\n"
    "- email\n\n"
    "Se for empresa, informe também o *CNPJ*."
)

MENSAGEM_PADRAO = (
    "Digite *OI* para iniciar o atendimento ou escolha uma opção do menu."
)

MENSAGEM_NAO_TEXTO = (
    "Por favor, envie sua solicitação em formato de texto para continuarmos o atendimento.\n\n"
    "Digite *OI* para abrir o menu."
)

# =========================
# FUNCOES
# =========================
def normalizar(texto):
    return texto.strip().lower() if texto else ""

def contem(texto, lista):
    return any(p in texto for p in lista)

def montar_resposta(texto):
    texto = normalizar(texto)

    if texto in PALAVRAS_MENU:
        return MENSAGEM_INICIAL

    # 🔥 NOVA ORDEM
    if texto == "1":
        return MENSAGEM_VENDAS

    if texto == "2":
        return MENSAGEM_SUPORTE

    if texto == "3":
        return MENSAGEM_ESPECIALISTA

    if contem(texto, PALAVRAS_CLIENTE_QUENTE):
        if "preco" in texto or "preço" in texto or "valor" in texto:
            return MENSAGEM_PRECO
        if "prazo" in texto or "entrega" in texto:
            return MENSAGEM_PRAZO
        if "estoque" in texto:
            return MENSAGEM_ESTOQUE
        return MENSAGEM_CLIENTE_QUENTE

    return MENSAGEM_PADRAO

def responder(numero, texto):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }

    try:
        r = requests.post(url, json=payload, headers=headers)
        print("ENVIADO:", r.status_code, r.text, flush=True)
    except Exception as e:
        print("ERRO:", e, flush=True)

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Erro", 403

    data = request.get_json(silent=True)

    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                if "statuses" in value:
                    continue

                for msg in value.get("messages", []):
                    numero = msg.get("from")
                    texto = msg.get("text", {}).get("body", "")

                    resposta = montar_resposta(texto)
                    responder(numero, resposta)

    except Exception as e:
        print("ERRO:", e, flush=True)

    return jsonify({"ok": True})

# =========================
# START
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
