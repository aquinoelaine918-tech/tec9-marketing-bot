from flask import Flask, request
import requests
import os
import threading
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


# =========================================================
# FUNÇÃO HOME
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

                texto = message["text"]["body"].strip().lower()

                print(f"MENSAGEM: {texto}")

                # =====================================================
                # MENU PRINCIPAL
                # =====================================================

                if texto in ["oi", "ola", "olá", "menu", "inicio", "início"]:

                    menu_inicial = (
                        "Olá 👋 Seja bem-vindo(a) à *TEC9 Informática* 🚀\n\n"
                        "Para agilizar seu atendimento, escolha uma opção:\n\n"
                        "1️⃣ Empresa / Pessoa Jurídica\n"
                        "2️⃣ Uso pessoal / Pessoa Física\n"
                        "3️⃣ Upgrade / SSD / peças\n\n"
                        "Digite o número correspondente 👇"
                    )

                    responder_mensagem(numero, menu_inicial)

                # =====================================================
                # PESSOA JURÍDICA
                # =====================================================

                elif texto == "1":

                    resposta_pj = (
                        "🏢 *Atendimento Pessoa Jurídica*\n\n"
                        "Para agilizar seu orçamento, envie:\n\n"
                        "📌 CNPJ\n"
                        "📌 Nome do responsável\n"
                        "📌 E-mail corporativo\n"
                        "📌 Produto ou solução desejada\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF\n\n"
                        "Nossa equipe comercial dará continuidade ao atendimento 🚀"
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
                        "📌 Cidade/UF\n"
                        "📌 E-mail para proposta (opcional)\n\n"
                        "Nossa equipe comercial dará continuidade ao atendimento 🚀"
                    )

                    responder_mensagem(numero, resposta_pf)

                # =====================================================
                # UPGRADE / PEÇAS
                # =====================================================

                elif texto == "3":

                    resposta_upgrade = (
                        "🔧 *Upgrade e Peças*\n\n"
                        "Me informe qual produto você procura.\n\n"
                        "Exemplos:\n"
                        "SSD\n"
                        "Memória\n"
                        "Fonte\n"
                        "Placa de vídeo\n"
                        "Notebook\n"
                        "Processador\n"
                    )

                    responder_mensagem(numero, resposta_upgrade)

                # =====================================================
                # IA SIMPLES DE BUSCA AUTOMÁTICA
                # =====================================================

                else:

                    # resposta rápida imediata
                    responder_mensagem(
                        numero,
                        "Perfeito 👍 estou verificando as opções disponíveis..."
                    )

                    # processamento separado
                    thread = threading.Thread(
                        target=processar_busca_produto,
                        args=(numero, texto)
                    )

                    thread.start()

    except Exception as erro:

        print("\n===================================")
        print("ERRO AO PROCESSAR:")
        print(erro)
        print("===================================\n")

    return "ok", 200


# =========================================================
# PROCESSAR PRODUTO
# =========================================================

def processar_busca_produto(numero, texto):

    try:

        time.sleep(1)

        produto = texto.replace(" ", "+")

        link_busca = f"{SITE_BUSCA}{produto}"

        mensagem = (
            f"🔎 Encontrei opções para: *{texto}*\n\n"
            f"Veja aqui:\n"
            f"{link_busca}\n\n"
            f"Se desejar ajuda para escolher o modelo ideal, "
            f"fale com nossa especialista 👇\n\n"
            f"{WHATSAPP_ESPECIALISTA}"
        )

        responder_mensagem(numero, mensagem)

    except Exception as erro:

        print("\n===================================")
        print("ERRO PROCESSAR BUSCA:")
        print(erro)
        print("===================================\n")


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

        print("\n===================================")
        print(f"STATUS ENVIO: {resposta.status_code}")
        print(f"RESPOSTA ENVIO: {resposta.text}")
        print("===================================\n")

    except Exception as erro:

        print("\n===================================")
        print("ERRO AO ENVIAR:")
        print(erro)
        print("===================================\n")


# =========================================================
# INICIAR SERVIDOR
# =========================================================

if __name__ == "__main__":

    porta = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=porta
    )
