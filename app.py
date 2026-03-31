import os
import re
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
# CONFIGURACOES
# =========================
PALAVRAS_CLIENTE_QUENTE = [
    "preco", "preço", "valor", "quanto custa", "orcamento", "orçamento",
    "prazo", "entrega", "estoque", "disponivel", "disponível",
    "pagamento", "pix", "boleto", "cartao", "cartão", "comprar",
    "cotacao", "cotação", "pedido", "frete", "urgente"
]

PALAVRAS_MENU = [
    "oi", "olá", "ola", "menu", "inicio", "início", "bom dia", "boa tarde", "boa noite"
]

# =========================
# TEXTOS
# =========================
MENSAGEM_INICIAL = (
    "Olá! Seja bem-vindo(a) à *TEC9 Informática*.\n\n"
    "Selecione uma opção:\n\n"
    "1 - *Suporte Técnico*\n"
    "2 - *Orçamentos e Vendas*\n"
    "3 - *Falar com Especialista*\n\n"
    "Digite o número da opção."
)

MENSAGEM_SUPORTE = (
    "🔧 *Suporte Técnico*\n\n"
    "Por favor, informe:\n"
    "- marca do equipamento\n"
    "- modelo do equipamento\n"
    "- qual a dúvida\n"
    "- defeito ou situação\n\n"
    "Nossa equipe técnica irá analisar."
)

# 🔥 TEXTO EXATAMENTE COMO VOCÊ PEDIU
MENSAGEM_VENDAS = (
    "💰 *Orçamentos e Vendas*\n\n"
    "Por favor, envie:\n\n"
    "- Nome\n"
    "- quantidade desejada\n"
    "- nome do produto ou modelo\n"
    "- email\n\n"
    "Se a compra for para empresa informe também o *CNPJ*.\n\n"
    "Assim conseguiremos encaminhar uma proposta mais precisa e rápida."
)

MENSAGEM_ESPECIALISTA = (
    "👤 *Especialista*\n\n"
    "Envie:\n"
    "- produto ou necessidade\n"
    "- quantidade\n"
    "- email\n\n"
    "Se for empresa, informe o *CNPJ*.\n\n"
    "Um especialista irá assumir seu atendimento."
)

MENSAGEM_PRECO = (
    "Para verificar *preço*, envie:\n\n"
    "- nome do produto ou modelo\n"
    "- quantidade desejada\n"
    "- email\n\n"
    "Se for empresa, informe também o *CNPJ*."
)

MENSAGEM_PRAZO = (
    "Para validar *prazo de entrega*, precisamos de:\n"
    "- produto\n"
    "- quantidade\n\n"
    "Envie esses dados para análise."
)

MENSAGEM_ESTOQUE = (
    "Para verificar *estoque*, envie:\n"
    "- produto ou modelo\n"
    "- quantidade\n\n"
    "Assim confirmamos disponibilidade."
)

MENSAGEM_CLIENTE_QUENTE = (
    "Perfeito, vamos agilizar seu atendimento.\n\n"
    "Envie:\n"
    "- Nome\n"
    "- quantidade desejada\n"
    "- produto ou modelo\n"
    "- email\n\n"
    "Se for empresa, informe o *CNPJ*.\n\n"
    "Nossa equipe irá analisar preço, prazo e disponibilidade."
)

MENSAGEM_PADRAO = (
    "Digite *OI* para iniciar o atendimento ou escolha uma opção do menu."
)

# =========================
# FUNCOES
# =========================
def normalizar_texto(texto):
    return texto.strip().lower() if texto else ""

def contem(texto, lista):
    return any(p in texto for p in lista)

def montar_resposta(texto):
    texto = normalizar_texto(texto)

    if texto in PALAVRAS_MENU:
        return MENSAGEM_INICIAL

    if texto == "1":
        return MENSAGEM_SUPORTE

    if texto == "2":
        return MENSAGEM_VENDAS

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
# ROTAS
# =========================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Erro", 403

    data = request.get_json(silent=True)
    print("DATA:", data, flush=True)

    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                # IGNORA STATUS
                if "statuses" in value:
                    continue

                for msg in value.get("messages", []):
                    numero = msg.get("from")
                    tipo = msg.get("type")

                    if tipo == "text":
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
