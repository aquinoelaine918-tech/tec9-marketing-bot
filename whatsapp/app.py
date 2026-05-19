from flask import Flask, request
import requests
import os

app = Flask(__name__)

# ==========================================
# CONFIGURAÇÕES
# ==========================================

VERIFY_TOKEN = "TEC9_TOKEN"

# TOKEN DO RAILWAY
WHATSAPP_TOKEN = os.getenv("META_ACCESS_TOKEN")

# PHONE NUMBER ID
PHONE_NUMBER_ID = "1099079283287430"


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    return "BOT ONLINE", 200


# ==========================================
# VERIFICAÇÃO WEBHOOK
# ==========================================

@app.route("/webhook", methods=["GET"])
def verify_webhook():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Erro de verificação", 403


# ==========================================
# RECEBER MENSAGENS
# ==========================================

@app.route("/webhook", methods=["POST"])
def receber_mensagem():

    data = request.get_json()

    print("EVENTO RECEBIDO:")
    print(data)

    try:

        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        messages = value.get("messages")

        if messages:

            message = messages[0]

            numero = message["from"]

            tipo = message["type"]

            print(f"TIPO: {tipo} DE: {numero}")

            if tipo == "text":

                texto = message["text"]["body"].strip().lower()

                print(f"MENSAGEM DE {numero}: {texto}")

                # ==========================================
                # MENU INICIAL
                # ==========================================

                if texto in ["oi", "olá", "ola", "menu", "inicio", "início"]:

                    resposta = """
🚀 Seja bem-vindo à TEC9 Informática!

Atendimento especializado em:
💻 Informática
🖨️ Automação
📡 Infraestrutura
📱 Tecnologia Corporativa

Para iniciarmos seu atendimento, escolha uma opção:

1️⃣ Pessoa Jurídica
2️⃣ Pessoa Física

Digite apenas o número da opção desejada 👇
"""

                    responder_mensagem(numero, resposta)

                # ==========================================
                # PESSOA JURÍDICA
                # ==========================================

                elif texto == "1":

                    resposta = """
🏢 Atendimento Pessoa Jurídica

Para agilizar sua cotação e análise comercial, envie as seguintes informações:

📌 CNPJ
📌 Nome do comprador/responsável
📌 E-mail corporativo
📌 Produto desejado
📌 Quantidade
📌 Cidade/UF para entrega

Após o envio, nossa equipe comercial continuará seu atendimento 🚀
"""

                    responder_mensagem(numero, resposta)

                # ==========================================
                # PESSOA FÍSICA
                # ==========================================

                elif texto == "2":

                    resposta = """
👤 Atendimento Pessoa Física

Para prosseguirmos com seu atendimento, envie:

📌 Nome completo
📌 Produto desejado
📌 Quantidade
📌 Cidade/UF para entrega
📌 E-mail (opcional)

Após o envio, nossa equipe continuará seu atendimento 🚀
"""

                    responder_mensagem(numero, resposta)

                # ==========================================
                # CONSULTA PRODUTOS
                # ==========================================

                elif "notebook" in texto:

                    resposta = """
💻 Trabalhamos com notebooks das principais marcas:

✅ Dell
✅ Lenovo
✅ HP
✅ Acer

Informe:
📌 Marca desejada
📌 Configuração
📌 Quantidade

Que já verificamos disponibilidade e valores 🚀
"""

                    responder_mensagem(numero, resposta)

                elif "impressora" in texto:

                    resposta = """
🖨️ Trabalhamos com impressoras:

✅ Epson
✅ Brother
✅ HP
✅ Zebra
✅ Elgin

Informe:
📌 Modelo desejado
📌 Quantidade
📌 Cidade de entrega
"""

                    responder_mensagem(numero, resposta)

                elif "coletor" in texto:

                    resposta = """
📦 Linha de Coletores disponíveis:

✅ Zebra
✅ Honeywell
✅ Chainway

Informe:
📌 Modelo desejado
📌 Quantidade
📌 Necessidade da operação

Nossa equipe especializada retornará 🚀
"""

                    responder_mensagem(numero, resposta)

                # ==========================================
                # FINALIZAÇÃO
                # ==========================================

                else:

                    resposta = """
❌ Não consegui identificar sua solicitação.

Escolha uma opção:

1️⃣ Pessoa Jurídica
2️⃣ Pessoa Física

Ou descreva o produto desejado 💬
"""

                    responder_mensagem(numero, resposta)

    except Exception as erro:

        print("ERRO AO PROCESSAR:")
        print(erro)

    return "ok", 200


# ==========================================
# ENVIAR RESPOSTA
# ==========================================

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

    resposta = requests.post(
        url,
        headers=headers,
        json=payload
    )

    print(f"STATUS ENVIO: {resposta.status_code}")
    print(f"RESPOSTA ENVIO: {resposta.text}")


# ==========================================
# EXECUÇÃO
# ==========================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
