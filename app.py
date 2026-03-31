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
WHATSAPP_HUMANO = (os.getenv("WHATSAPP_HUMANO") or "").strip()

# =========================
# AGENTES TEC9
# =========================
AGENTE_SUPORTE = "Lucas"
AGENTE_VENDAS = "Camila"
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

PALAVRAS_PJ = [
    "empresa", "cnpj", "pj", "corporativo", "revenda", "faturamento"
]

# =========================
# TEXTOS
# =========================
MENSAGEM_INICIAL = (
    "Olá! Seja bem-vindo(a) à *TEC9 Informática*.\n\n"
    "Você será atendido(a) por nossa equipe especializada:\n\n"
    f"1 - *{AGENTE_SUPORTE}* | Suporte Técnico\n"
    f"2 - *{AGENTE_VENDAS}* | Orçamentos e Vendas\n"
    f"3 - *{AGENTE_ESPECIALISTA}* | Especialista TEC9\n\n"
    "Digite apenas o número da opção desejada."
)

MENSAGEM_SUPORTE = (
    f"🔧 *{AGENTE_SUPORTE} | Suporte Técnico TEC9*\n\n"
    "Vou dar sequência ao seu atendimento.\n\n"
    "Por favor, informe:\n"
    "- marca do equipamento\n"
    "- modelo do equipamento\n"
    "- qual a dúvida\n"
    "- defeito ou situação apresentada\n\n"
    "Nossa equipe técnica irá analisar sua solicitação com atenção."
)

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

MENSAGEM_ESPECIALISTA = (
    f"👤 *{AGENTE_ESPECIALISTA} | Especialista TEC9*\n\n"
    "Vou assumir seu atendimento a partir deste momento.\n\n"
    "Para agilizar a análise, envie por favor:\n"
    "- nome\n"
    "- produto ou necessidade\n"
    "- quantidade\n"
    "- email\n\n"
    "Se for atendimento corporativo, informe também o *CNPJ*.\n\n"
    "Em seguida, daremos continuidade com prioridade."
)

MENSAGEM_PRECO = (
    f"💰 *{AGENTE_VENDAS} | Consultora Comercial TEC9*\n\n"
    "Perfeito. Para verificarmos *preço e proposta comercial*, envie por favor:\n\n"
    "- Nome\n"
    "- quantidade desejada\n"
    "- nome do produto ou modelo\n"
    "- email\n\n"
    "Se a compra for para empresa, informe também o *CNPJ*.\n\n"
    "Assim conseguimos analisar sua solicitação com mais precisão."
)

MENSAGEM_PRAZO = (
    f"🚚 *{AGENTE_VENDAS} | Consultora Comercial TEC9*\n\n"
    "Perfeito. Para validarmos *prazo, disponibilidade e entrega*, envie por favor:\n\n"
    "- Nome\n"
    "- quantidade desejada\n"
    "- nome do produto ou modelo\n"
    "- email\n\n"
    "Se for compra para empresa, informe também o *CNPJ*."
)

MENSAGEM_ESTOQUE = (
    f"📦 *{AGENTE_VENDAS} | Consultora Comercial TEC9*\n\n"
    "Perfeito. Para confirmarmos *estoque e disponibilidade*, envie por favor:\n\n"
    "- Nome\n"
    "- quantidade desejada\n"
    "- nome do produto ou modelo\n"
    "- email\n\n"
    "Se a compra for para empresa, informe também o *CNPJ*."
)

MENSAGEM_CLIENTE_QUENTE = (
    f"🔥 *{AGENTE_VENDAS} | Atendimento Comercial Prioritário*\n\n"
    "Identificamos sua solicitação como *atendimento comercial prioritário*.\n\n"
    "Para que nossa equipe avance com mais agilidade, envie por favor:\n\n"
    "- Nome\n"
    "- quantidade desejada\n"
    "- nome do produto ou modelo\n"
    "- email\n\n"
    "Se a compra for para empresa, informe também o *CNPJ*.\n\n"
    "Assim conseguiremos encaminhar sua proposta com mais precisão e rapidez."
)

MENSAGEM_PJ = (
    f"🏢 *{AGENTE_VENDAS} | Atendimento Corporativo TEC9*\n\n"
    "Perfeito. Para atendimento corporativo, envie por favor:\n\n"
    "- Nome do responsável\n"
    "- quantidade desejada\n"
    "- nome do produto ou modelo\n"
    "- email\n"
    "- CNPJ\n\n"
    "Assim conseguiremos encaminhar uma proposta empresarial com mais agilidade."
)

MENSAGEM_LEAD_QUALIFICADO = (
    f"✅ *{AGENTE_VENDAS} | Consultora Comercial TEC9*\n\n"
    "Perfeito. Recebemos suas informações.\n\n"
    "Sua solicitação foi encaminhada para *atendimento comercial especializado*.\n"
    "Nossa equipe dará continuidade com a análise da proposta e retornará com as informações necessárias."
)

MENSAGEM_PADRAO = (
    "Recebemos sua mensagem.\n\n"
    "Para continuar, digite:\n\n"
    f"1 - *{AGENTE_SUPORTE}* | Suporte Técnico\n"
    f"2 - *{AGENTE_VENDAS}* | Orçamentos e Vendas\n"
    f"3 - *{AGENTE_ESPECIALISTA}* | Especialista TEC9\n\n"
    "Ou digite *OI* para visualizar novamente o menu."
)

MENSAGEM_NAO_TEXTO = (
    "Recebemos sua mensagem.\n\n"
    "No momento, pedimos por gentileza que envie sua solicitação em formato de texto para darmos continuidade ao atendimento.\n\n"
    "Digite *OI* para visualizar o menu principal."
)

# =========================
# FUNCOES AUXILIARES
# =========================
def normalizar_texto(texto):
    return texto.strip().lower() if texto else ""

def contem_palavra(texto, palavras):
    texto_norm = normalizar_texto(texto)
    return any(p in texto_norm for p in palavras)

def parece_lead_qualificado(texto):
    texto_norm = normalizar_texto(texto)
    tem_email = "@" in texto_norm
    tem_numero = any(char.isdigit() for char in texto_norm)
    return tem_email and tem_numero

def montar_resposta(texto):
    texto_norm = normalizar_texto(texto)

    if texto_norm in PALAVRAS_MENU:
        return MENSAGEM_INICIAL

    if texto_norm == "1":
        return MENSAGEM_SUPORTE

    if texto_norm == "2":
        return MENSAGEM_VENDAS

    if texto_norm == "3":
        return MENSAGEM_ESPECIALISTA

    if contem_palavra(texto_norm, PALAVRAS_PJ):
        return MENSAGEM_PJ

    if parece_lead_qualificado(texto_norm):
        return MENSAGEM_LEAD_QUALIFICADO

    if contem_palavra(texto_norm, PALAVRAS_CLIENTE_QUENTE):
        if any(p in texto_norm for p in ["preco", "preço", "valor", "quanto custa", "orcamento", "orçamento", "cotacao", "cotação"]):
            return MENSAGEM_PRECO

        if any(p in texto_norm for p in ["prazo", "entrega", "frete"]):
            return MENSAGEM_PRAZO

        if any(p in texto_norm for p in ["estoque", "disponivel", "disponível"]):
            return MENSAGEM_ESTOQUE

        return MENSAGEM_CLIENTE_QUENTE

    return MENSAGEM_PADRAO

def responder(numero, texto):
    if not ACCESS_TOKEN:
        print("META_ACCESS_TOKEN nao configurado", flush=True)
        return

    if not PHONE_NUMBER_ID:
        print("PHONE_NUMBER_ID nao configurado", flush=True)
        return

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
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        print("ENVIADO:", r.status_code, r.text, flush=True)
    except Exception as e:
        print("ERRO AO ENVIAR:", str(e), flush=True)

# =========================
# ROTAS
# =========================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "verify_token_configurado": bool(VERIFY_TOKEN),
        "access_token_configurado": bool(ACCESS_TOKEN),
        "phone_number_id_configurado": bool(PHONE_NUMBER_ID),
        "whatsapp_humano_configurado": bool(WHATSAPP_HUMANO)
    }), 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        print("VALIDACAO RECEBIDA", flush=True)
        print("hub.mode:", mode, flush=True)
        print("hub.verify_token:", token, flush=True)

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK VALIDADO COM SUCESSO", flush=True)
            return challenge, 200

        return "Erro de verificacao", 403

    data = request.get_json(silent=True)
    print("WEBHOOK RECEBIDO:", data, flush=True)

    try:
        if not data:
            return jsonify({"status": "no data"}), 200

        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                if "statuses" in value:
                    print("STATUS IGNORADO:", value.get("statuses"), flush=True)
                    continue

                if "messages" not in value:
                    print("Evento ignorado (sem mensagem)", flush=True)
                    continue

                for msg in value.get("messages", []):
                    numero = msg.get("from")
                    tipo = msg.get("type", "")

                    if not numero:
                        print("Mensagem sem remetente, ignorada.", flush=True)
                        continue

                    if tipo == "text":
                        texto = msg.get("text", {}).get("body", "").strip()
                        print(f"MENSAGEM DE {numero}: {texto}", flush=True)

                        resposta = montar_resposta(texto)
                        responder(numero, resposta)
                    else:
                        print(f"MENSAGEM NAO TEXTO DE {numero}: {tipo}", flush=True)
                        responder(numero, MENSAGEM_NAO_TEXTO)

    except Exception as e:
        print("ERRO AO PROCESSAR WEBHOOK:", str(e), flush=True)

    return jsonify({"ok": True}), 200

# =========================
# START
# =========================
if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 3000))
    print(f"Servidor iniciando na porta {porta}", flush=True)
    app.run(host="0.0.0.0", port=porta)
