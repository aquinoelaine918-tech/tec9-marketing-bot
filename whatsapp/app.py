from flask import Flask, request
import requests
import os
import time

app = Flask(__name__)

# =========================================================
# CONFIGURAÇÕES
# =========================================================

VERIFY_TOKEN = "TEC9_TOKEN"

WHATSAPP_TOKEN = os.getenv("META_ACCESS_TOKEN")

PHONE_NUMBER_ID = "1099079283287430"

SITE_BUSCA = "https://tec9informatica.com.br/busca?q="

WHATSAPP_ESPECIALISTA = "https://wa.me/5511977315223"

HORARIO_ATENDIMENTO = (
    "🕘 Horário de atendimento:\n"
    "Segunda a Sexta-feira\n"
    "Das 09:00 às 18:00"
)

# =========================================================
# PALAVRAS IMPORTANTES
# =========================================================

SAUDACOES = [
    "oi",
    "ola",
    "olá",
    "bom dia",
    "boa tarde",
    "boa noite",
    "menu",
    "inicio",
    "início"
]

PALAVRAS_EMPRESA = [
    "empresa",
    "cnpj",
    "corporativo",
    "servidor",
    "infraestrutura",
    "licitação",
    "licitacao",
    "volume"
]

PALAVRAS_QUENTES = [
    "comprar",
    "orcamento",
    "orçamento",
    "desconto",
    "pedido",
    "fechar",
    "pix",
    "urgente",
    "proposta"
]

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return "TEC9 BOT ONLINE 🚀", 200

# =========================================================
# VERIFICAÇÃO META
# =========================================================

@app.route("/webhook", methods=["GET"])
def verify_webhook():

    mode = request.args.get("hub.mode")

    token = request.args.get("hub.verify_token")

    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:

        return challenge, 200

    return "Erro de verificação", 403

# =========================================================
# RECEBER MENSAGEM
# =========================================================

@app.route("/webhook", methods=["POST"])
def receber_mensagem():

    data = request.get_json()

    print("\n================================================")
    print("EVENTO RECEBIDO")
    print(data)
    print("================================================\n")

    try:

        entry = data["entry"][0]

        changes = entry["changes"][0]

        value = changes["value"]

        messages = value.get("messages")

        if messages:

            message = messages[0]

            numero = message["from"]

            tipo = message["type"]

            print(f"TIPO: {tipo}")

            if tipo == "text":

                texto_original = message["text"]["body"].strip()

                texto = texto_original.lower()

                print(f"MENSAGEM: {texto}")

                # =====================================================
                # MENU PRINCIPAL
                # =====================================================

                if texto in SAUDACOES:

                    enviar_menu(numero)

                # =====================================================
                # PESSOA JURÍDICA
                # =====================================================

                elif texto == "1":

                    resposta_pj = (
                        "🏢 *Atendimento Pessoa Jurídica*\n\n"
                        "Para agilizar seu atendimento, envie:\n\n"
                        "📌 CNPJ\n"
                        "📌 Nome do responsável\n"
                        "📌 E-mail\n"
                        "📌 Produto desejado\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF\n\n"
                        "Nossa equipe comercial dará continuidade ao atendimento 🚀\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, resposta_pj)

                # =====================================================
                # PESSOA FÍSICA
                # =====================================================

                elif texto == "2":

                    resposta_pf = (
                        "👤 *Atendimento Pessoa Física*\n\n"
                        "Para prosseguirmos com seu atendimento, envie:\n\n"
                        "📌 Nome\n"
                        "📌 Produto desejado\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF\n\n"
                        "Nossa equipe comercial dará continuidade ao atendimento 🚀\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, resposta_pf)

                # =====================================================
                # UPGRADE / PEÇAS
                # =====================================================

                elif texto == "3":

                    resposta_upgrade = (
                        "🔧 *Upgrade / SSD / Peças*\n\n"
                        "Digite o produto desejado.\n\n"
                        "Exemplos:\n\n"
                        "• SSD\n"
                        "• Memória\n"
                        "• Fonte\n"
                        "• Notebook\n"
                        "• Processador\n"
                        "• Placa de vídeo\n"
                        "• Gabinete\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, resposta_upgrade)

                # =====================================================
                # DETECTAR CNPJ
                # =====================================================

                elif detectar_cnpj(texto):

                    resposta_cnpj = (
                        "🏢 Identificamos um possível atendimento corporativo.\n\n"
                        "Nossa equipe comercial dará continuidade ao atendimento.\n\n"
                        "Para atendimento especializado 👇\n\n"
                        f"{WHATSAPP_ESPECIALISTA}\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, resposta_cnpj)

                # =====================================================
                # CLIENTE QUENTE
                # =====================================================

                elif detectar_cliente_quente(texto):

                    resposta_quente = (
                        "🔥 Identificamos interesse comercial.\n\n"
                        "Para um atendimento mais rápido e personalizado, "
                        "fale diretamente com nossa especialista 👇\n\n"
                        f"{WHATSAPP_ESPECIALISTA}\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, resposta_quente)

                # =====================================================
                # EMPRESA
                # =====================================================

                elif detectar_empresa(texto):

                    resposta_empresa = (
                        "🏢 Identificamos um atendimento corporativo.\n\n"
                        "Para atendimento especializado 👇\n\n"
                        f"{WHATSAPP_ESPECIALISTA}\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, resposta_empresa)

                # =====================================================
                # BUSCA AUTOMÁTICA
                # =====================================================

                else:

                    busca = texto.replace(" ", "+")

                    link_busca = f"{SITE_BUSCA}{busca}"

                    resposta_produto = (
                        f"🔎 Separei algumas opções relacionadas a: *{texto_original}*\n\n"
                        f"Confira aqui 😊\n\n"
                        f"{link_busca}\n\n"
                        f"Se desejar ajuda para escolher o modelo ideal 👇\n"
                        f"{WHATSAPP_ESPECIALISTA}\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, resposta_produto)

    except Exception as erro:

        print("\n================================================")
        print("ERRO AO PROCESSAR")
        print(erro)
        print("================================================\n")

    return "ok", 200

# =========================================================
# MENU PRINCIPAL
# =========================================================

def enviar_menu(numero):

    mensagem = (
        "Olá 👋 Seja bem-vindo(a) à *TEC9 Informática* 🚀\n\n"
        "Para agilizar seu atendimento, escolha uma opção:\n\n"
        "1️⃣ Pessoa Jurídica\n"
        "2️⃣ Pessoa Física\n"
        "3️⃣ Upgrade / SSD / peças\n\n"
        "Ou digite diretamente o produto que procura 👇\n\n"
        f"{HORARIO_ATENDIMENTO}"
    )

    responder_mensagem(numero, mensagem)

# =========================================================
# DETECTAR CLIENTE QUENTE
# =========================================================

def detectar_cliente_quente(texto):

    for palavra in PALAVRAS_QUENTES:

        if palavra in texto:

            return True

    return False

# =========================================================
# DETECTAR EMPRESA
# =========================================================

def detectar_empresa(texto):

    for palavra in PALAVRAS_EMPRESA:

        if palavra in texto:

            return True

    return False

# =========================================================
# DETECTAR CNPJ
# =========================================================

def detectar_cnpj(texto):

    numeros = ""

    for caractere in texto:

        if caractere.isdigit():

            numeros += caractere

    if len(numeros) >= 11:

        return True

    return False

# =========================================================
# ENVIAR WHATSAPP
# =========================================================

def responder_mensagem(numero, mensagem):

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": mensagem
        }
    }

    try:

        resposta = requests.post(
            url,
            headers=headers,
            json=payload
        )

        print("\n================================================")
        print(f"STATUS ENVIO: {resposta.status_code}")
        print(f"RESPOSTA ENVIO: {resposta.text}")
        print("================================================\n")

        time.sleep(1)

    except Exception as erro:

        print("\n================================================")
        print("ERRO AO ENVIAR")
        print(erro)
        print("================================================\n")

# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    porta = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=porta
    )
