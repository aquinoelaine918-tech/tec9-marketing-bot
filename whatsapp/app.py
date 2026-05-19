from flask import Flask, request
import requests
import os

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
    "🕘 *Horário de atendimento TEC9 Informática*\n"
    "Segunda a Sexta-feira\n"
    "Das 09:00 às 18:00"
)

# =========================================================
# PALAVRAS IMPORTANTES
# =========================================================

saudacoes = [
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

palavras_quentes = [
    "comprar",
    "orcamento",
    "orçamento",
    "desconto",
    "fechar",
    "pedido",
    "pix",
    "urgente"
]

palavras_empresa = [
    "empresa",
    "cnpj",
    "corporativo",
    "servidor",
    "infraestrutura"
]

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return "TEC9 BOT ONLINE 🚀", 200

# =========================================================
# VERIFICAÇÃO WEBHOOK META
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
# RECEBER MENSAGENS
# =========================================================

@app.route("/webhook", methods=["POST"])
def receber_mensagem():

    data = request.get_json()

    print("\n================================================")
    print("EVENTO RECEBIDO:")
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
            print(f"NUMERO: {numero}")

            if tipo == "text":

                texto_original = message["text"]["body"].strip()

                texto = texto_original.lower()

                print(f"MENSAGEM: {texto}")

                # =====================================================
                # MENU INICIAL
                # =====================================================

                if texto in saudacoes:

                    menu = (
                        "Olá 👋 Seja bem-vindo(a) à *TEC9 Informática* 🚀\n\n"
                        "Escolha uma opção:\n\n"
                        "1️⃣ Pessoa Jurídica\n"
                        "2️⃣ Pessoa Física\n"
                        "3️⃣ Upgrade / SSD / peças\n\n"
                        "Ou digite diretamente o produto que procura 👇\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, menu)

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
                        "🔧 *Upgrade e Peças*\n\n"
                        "Digite o produto desejado.\n\n"
                        "Exemplos:\n"
                        "SSD\n"
                        "Memória\n"
                        "Fonte\n"
                        "Notebook\n"
                        "Processador\n"
                        "Placa de vídeo\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, resposta_upgrade)

                # =====================================================
                # CLIENTE QUENTE
                # =====================================================

                elif any(palavra in texto for palavra in palavras_quentes):

                    mensagem_quente = (
                        "🔥 Identificamos interesse comercial.\n\n"
                        "Para agilizar seu atendimento e verificar condições especiais, "
                        "fale diretamente com nossa especialista 👇\n\n"
                        f"{WHATSAPP_ESPECIALISTA}\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, mensagem_quente)

                # =====================================================
                # EMPRESA AUTOMÁTICO
                # =====================================================

                elif any(palavra in texto for palavra in palavras_empresa):

                    mensagem_empresa = (
                        "🏢 Atendimento corporativo identificado.\n\n"
                        "Para um atendimento especializado 👇\n\n"
                        f"{WHATSAPP_ESPECIALISTA}\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, mensagem_empresa)

                # =====================================================
                # BUSCA AUTOMÁTICA PRODUTO
                # =====================================================

                else:

                    busca = texto.replace(" ", "+")

                    link_busca = f"{SITE_BUSCA}{busca}"

                    mensagem_produto = (
                        f"🔎 Encontrei opções relacionadas a: *{texto_original}*\n\n"
                        f"Confira aqui:\n"
                        f"{link_busca}\n\n"
                        f"Se desejar ajuda para escolher o modelo ideal 👇\n"
                        f"{WHATSAPP_ESPECIALISTA}\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, mensagem_produto)

    except Exception as erro:

        print("\n================================================")
        print("ERRO AO PROCESSAR:")
        print(erro)
        print("================================================\n")

    return "ok", 200

# =========================================================
# ENVIAR MENSAGEM WHATSAPP
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

    except Exception as erro:

        print("\n================================================")
        print("ERRO AO ENVIAR:")
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
