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

PALAVRAS_PJ = [
    "cnpj", "empresa", "pj", "pessoa juridica", "pessoa jurídica",
    "corporativo", "revenda", "faturamento"
]

PALAVRAS_MENU = [
    "oi", "olá", "ola", "menu", "inicio", "início", "bom dia", "boa tarde", "boa noite"
]

# =========================
# TEXTOS PROFISSIONAIS
# =========================
MENSAGEM_INICIAL = (
    "Olá! Seja bem-vindo(a) à *TEC9 Informática*.\n\n"
    "Atendemos clientes *Pessoa Física* e *Empresas* com soluções em tecnologia, "
    "equipamentos, suprimentos e atendimento especializado.\n\n"
    "Selecione uma das opções abaixo para continuar:\n\n"
    "1 - *Suporte Técnico*\n"
    "2 - *Orçamentos e Vendas*\n"
    "3 - *Atendimento com Especialista*\n\n"
    "Por favor, digite apenas o número da opção desejada."
)

MENSAGEM_SUPORTE = (
    "Você selecionou *Suporte Técnico*.\n\n"
    "Por favor, descreva o problema do equipamento com o máximo de detalhes possível, informando:\n"
    "- marca\n"
    "- modelo\n"
    "- defeito apresentado\n"
    "- quando o problema começou\n\n"
    "Nossa equipe técnica analisará sua solicitação com a máxima atenção."
)

MENSAGEM_VENDAS = (
    "Você selecionou *Orçamentos e Vendas*.\n\n"
    "Para agilizar seu atendimento, envie por favor:\n"
    "- nome do produto ou modelo\n"
    "- quantidade desejada\n"
    "- cidade de entrega\n"
    "- nome completo\n"
    "- email para envio da proposta\n\n"
    "Se a compra for para *empresa*, informe também o *CNPJ*.\n\n"
    "Assim conseguiremos encaminhar uma proposta mais precisa e rápida."
)

MENSAGEM_ESPECIALISTA = (
    "Você selecionou *Atendimento com Especialista*.\n\n"
    "Para darmos continuidade com mais agilidade, envie por favor:\n"
    "- seu nome\n"
    "- produto ou necessidade\n"
    "- quantidade\n"
    "- cidade de entrega\n"
    "- email\n\n"
    "Se o atendimento for corporativo, informe também o *CNPJ da empresa*.\n\n"
    "Em seguida, um especialista da *TEC9 Informática* dará sequência ao seu atendimento."
)

MENSAGEM_NAO_TEXTO = (
    "Recebemos sua mensagem.\n\n"
    "No momento, para melhor direcionamento do atendimento, pedimos por gentileza que envie sua solicitação em formato de texto.\n\n"
    "Digite *OI* para visualizar o menu principal."
)

MENSAGEM_PADRAO = (
    "Recebemos sua mensagem com sucesso.\n\n"
    "Para direcionarmos seu atendimento da melhor forma, escolha uma das opções abaixo:\n\n"
    "1 - *Suporte Técnico*\n"
    "2 - *Orçamentos e Vendas*\n"
    "3 - *Atendimento com Especialista*\n\n"
    "Se preferir, digite *OI* para visualizar novamente o menu principal."
)

MENSAGEM_CLIENTE_QUENTE = (
    "Perfeito. Identificamos que sua solicitação é de *atendimento comercial prioritário*.\n\n"
    "Para que nossa equipe comercial envie uma proposta com mais agilidade, por favor responda com as seguintes informações:\n\n"
    "- nome do produto ou modelo\n"
    "- quantidade desejada\n"
    "- cidade de entrega\n"
    "- nome completo\n"
    "- email\n\n"
    "Se for compra para *empresa*, informe também:\n"
    "- *CNPJ*\n"
    "- razão social, se desejar\n\n"
    "Assim conseguimos analisar *preço, prazo, estoque e entrega* com mais precisão."
)

MENSAGEM_PRECO = (
    "Sobre *preço e orçamento*: trabalhamos com atendimento consultivo para encontrar a melhor condição conforme produto, quantidade e disponibilidade.\n\n"
    "Para cotação mais precisa, envie por favor:\n"
    "- produto ou modelo\n"
    "- quantidade\n"
    "- cidade de entrega\n"
    "- nome\n"
    "- email\n\n"
    "Se a compra for para empresa, informe também o *CNPJ*."
)

MENSAGEM_PRAZO = (
    "Sobre *prazo e entrega*: o prazo pode variar conforme disponibilidade do item, volume do pedido, forma de pagamento e CEP de destino.\n\n"
    "Para validarmos corretamente, envie:\n"
    "- produto ou modelo\n"
    "- quantidade\n"
    "- cidade ou CEP de entrega\n"
    "- nome\n"
    "- email\n\n"
    "Se for atendimento corporativo, informe também o *CNPJ*."
)

MENSAGEM_ESTOQUE = (
    "Sobre *estoque e disponibilidade*: a confirmação depende do modelo exato, quantidade solicitada e disponibilidade no momento da consulta.\n\n"
    "Para verificarmos com precisão, envie:\n"
    "- produto ou modelo\n"
    "- quantidade desejada\n"
    "- cidade de entrega\n"
    "- nome\n"
    "- email\n\n"
    "Se a compra for para empresa, informe também o *CNPJ*."
)

MENSAGEM_ENCAMINHAMENTO_HUMANO = (
    "Sua solicitação foi classificada para *atendimento comercial especializado*.\n\n"
    "Nossa equipe dará continuidade para analisar:\n"
    "- melhor condição comercial\n"
    "- disponibilidade\n"
    "- prazo de entrega\n"
    "- proposta personalizada\n\n"
    "Para agilizar ainda mais, envie todas as informações do pedido nesta conversa.\n\n"
    "Um vendedor da *TEC9 Informática* dará sequência ao seu atendimento."
)

MENSAGEM_PJ_REFORCO = (
    "Identificamos que seu atendimento pode ser *corporativo*.\n\n"
    "Para elaboração da proposta empresarial, pedimos por gentileza o envio de:\n"
    "- nome do responsável\n"
    "- email\n"
    "- produto ou necessidade\n"
    "- quantidade\n"
    "- cidade de entrega\n"
    "- *CNPJ da empresa*\n\n"
    "Com isso conseguimos agilizar a análise comercial e o envio da proposta."
)

# =========================
# FUNCOES AUXILIARES
# =========================
def normalizar_texto(texto):
    if not texto:
        return ""
    texto = texto.strip().lower()
    return texto

def contem_termo(texto, lista_termos):
    texto_norm = normalizar_texto(texto)
    for termo in lista_termos:
        if termo in texto_norm:
            return True
    return False

def extrair_email(texto):
    if not texto:
        return None
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', texto)
    return match.group(0) if match else None

def extrair_cnpj(texto):
    if not texto:
        return None
    match = re.search(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', texto)
    return match.group(0) if match else None

def tem_dados_basicos(texto):
    email = extrair_email(texto)
    cnpj = extrair_cnpj(texto)
    return {
        "email_encontrado": bool(email),
        "cnpj_encontrado": bool(cnpj)
    }

def montar_resposta(texto_recebido):
    texto = normalizar_texto(texto_recebido)
    dados = tem_dados_basicos(texto)

    # Menu principal
    if texto in PALAVRAS_MENU:
        return MENSAGEM_INICIAL

    # Opcoes numericas
    if texto == "1":
        return MENSAGEM_SUPORTE

    if texto == "2":
        return MENSAGEM_VENDAS

    if texto == "3":
        return MENSAGEM_ESPECIALISTA

    # Se o cliente mencionar empresa / PJ / CNPJ
    if contem_termo(texto, PALAVRAS_PJ):
        if not dados["cnpj_encontrado"]:
            return MENSAGEM_PJ_REFORCO
        return (
            "Perfeito. Recebemos a indicação de atendimento corporativo.\n\n"
            "Nossa equipe comercial irá prosseguir com a análise da sua demanda.\n"
            "Se possível, envie também:\n"
            "- produto ou modelo\n"
            "- quantidade\n"
            "- cidade de entrega\n"
            "- nome do responsável\n"
            "- email\n\n"
            "Com isso conseguimos acelerar a proposta."
        )

    # Cliente quente: preço, prazo, estoque, entrega, pagamento etc.
    if contem_termo(texto, PALAVRAS_CLIENTE_QUENTE):
        # respostas mais específicas
        if any(termo in texto for termo in ["preco", "preço", "valor", "quanto custa", "orcamento", "orçamento", "cotacao", "cotação"]):
            return MENSAGEM_PRECO

        if any(termo in texto for termo in ["prazo", "entrega", "frete"]):
            return MENSAGEM_PRAZO

        if any(termo in texto for termo in ["estoque", "disponivel", "disponível"]):
            return MENSAGEM_ESTOQUE

        return MENSAGEM_CLIENTE_QUENTE

    # Caso o cliente já mande bastante informação
    if dados["email_encontrado"] and dados["cnpj_encontrado"]:
        return (
            "Perfeito. Recebemos seus dados para atendimento corporativo.\n\n"
            "Nossa equipe comercial dará andamento à análise de *preço, prazo, estoque e entrega*.\n"
            "Se ainda não enviou, por favor informe também:\n"
            "- produto ou modelo\n"
            "- quantidade desejada\n"
            "- cidade ou CEP de entrega\n\n"
            "Em seguida, um vendedor da *TEC9 Informática* continuará seu atendimento."
        )

    if dados["email_encontrado"]:
        return (
            "Perfeito. Recebemos seu email para continuidade do atendimento.\n\n"
            "Agora, para avançarmos com sua solicitação, envie por favor:\n"
            "- produto ou modelo\n"
            "- quantidade\n"
            "- cidade ou CEP de entrega\n\n"
            "Se a compra for para empresa, informe também o *CNPJ*.\n\n"
            + MENSAGEM_ENCAMINHAMENTO_HUMANO
        )

    # fallback profissional
    return MENSAGEM_PADRAO

def responder_mensagem(numero, texto):
    if not ACCESS_TOKEN:
        print("META_ACCESS_TOKEN nao configurado", flush=True)
        return

    if not PHONE_NUMBER_ID:
        print("PHONE_NUMBER_ID nao configurado", flush=True)
        return

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": texto
        }
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print("STATUS ENVIO:", response.status_code, flush=True)
        print("RESPOSTA META:", response.text, flush=True)
    except Exception as e:
        print("ERRO AO ENVIAR RESPOSTA:", str(e), flush=True)

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
        "phone_number_id_configurado": bool(PHONE_NUMBER_ID)
    }), 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # ---------------------------------
    # VALIDACAO DO WEBHOOK
    # ---------------------------------
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        print("VALIDACAO RECEBIDA", flush=True)
        print("hub.mode:", mode, flush=True)
        print("hub.verify_token:", token, flush=True)
        print("VERIFY_TOKEN:", VERIFY_TOKEN, flush=True)

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK VALIDADO COM SUCESSO", flush=True)
            return challenge, 200

        print("ERRO DE VERIFICACAO DO WEBHOOK", flush=True)
        return "Erro de verificacao", 403

    # ---------------------------------
    # RECEBIMENTO DE EVENTOS
    # ---------------------------------
    data = request.get_json(silent=True)
    print("WEBHOOK RECEBIDO:", data, flush=True)

    try:
        if not data:
            return jsonify({"status": "no data"}), 200

        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                # Ignora status da Meta
                if "statuses" in value:
                    print("STATUS IGNORADO:", value.get("statuses"), flush=True)
                    continue

                # Processa apenas mensagens
                if "messages" not in value:
                    print("Evento ignorado (sem mensagem)", flush=True)
                    continue

                for message in value.get("messages", []):
                    from_number = message.get("from")
                    message_type = message.get("type", "")

                    if not from_number:
                        print("Mensagem sem remetente, ignorada.", flush=True)
                        continue

                    # Processa mensagem de texto
                    if message_type == "text":
                        text_body = message.get("text", {}).get("body", "").strip()
                        print(f"MENSAGEM RECEBIDA DE {from_number}: {text_body}", flush=True)

                        resposta = montar_resposta(text_body)
                        responder_mensagem(from_number, resposta)

                    else:
                        print(f"MENSAGEM NAO TEXTO DE {from_number}: {message_type}", flush=True)
                        responder_mensagem(from_number, MENSAGEM_NAO_TEXTO)

    except Exception as e:
        print("ERRO AO PROCESSAR WEBHOOK:", str(e), flush=True)

    return jsonify({"status": "received"}), 200

# =========================
# INICIALIZACAO
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"Servidor iniciando na porta {port}", flush=True)
    app.run(host="0.0.0.0", port=port)
