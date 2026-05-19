from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "TEC9_TOKEN"
WHATSAPP_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = "1099079283287430"

# Dicionário na memória para controlar o fluxo de cada cliente
estados_clientes = {}

@app.route("/")
def home():
    return "BOT ONLINE", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Erro de verificação", 403

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
                texto_cliente = message["text"]["body"].strip()
                print(f"MENSAGEM DE {numero}: {texto_cliente}")

                # LÓGICA DOS 3 FLUXOS DE ATENDIMENTO
                estado_atual = estados_clientes.get(numero, "inicio")

                if estado_atual == "inicio":
                    # Bloco 1: Menu Inicial
                    menu_inicial = (
                        "Olá, seja bem-vindo à TEC9 Informática 🚀\n\n"
                        "Para iniciarmos seu atendimento, selecione uma opção:\n\n"
                        "1️⃣ Pessoa Jurídica\n"
                        "2️⃣ Pessoa Física\n\n"
                        "Digite o número correspondente 👇"
                    )
                    responder_mensagem(numero, menu_inicial)
                    estados_clientes[numero] = "aguardando_opcao"

                elif estado_atual == "aguardando_opcao":
                    if texto_cliente == "1":
                        # Bloco 2: Pessoa Jurídica
                        resposta_pj = (
                            "🏢 *Atendimento Pessoa Jurídica*\n\n"
                            "Para agilizar seu orçamento e atendimento corporativo, envie as informações abaixo:\n\n"
                            "📌 CNPJ\n"
                            "📌 Nome do comprador/responsável\n"
                            "📌 E-mail corporativo\n"
                            "📌 Produto ou solução desejada\n"
                            "📌 Quantidade\n"
                            "📌 Cidade/UF para entrega\n\n"
                            "Após o envio, nossa equipe comercial dará continuidade ao atendimento 🚀"
                        )
                        responder_mensagem(numero, resposta_pj)
                        estados_clientes[numero] = "dados_enviados"

                    elif texto_cliente == "2":
                        # Bloco 3: Pessoa Física
                        resposta_pf = (
                            "👤 *Atendimento Pessoa Física*\n\n"
                            "Para prosseguirmos com seu atendimento, envie:\n\n"
                            "📌 Nome\n"
                            "📌 Produto desejado\n"
                            "📌 Quantidade\n"
                            "📌 Cidade/UF para entrega\n"
                            "📌 E-mail para envio da proposta (opcional)\n\n"
                            "Após o envio, nossa equipe comercial dará continuidade ao atendimento 🚀"
                        )
                        responder_mensagem(numero, resposta_pf)
                        estados_clientes[numero] = "dados_enviados"

                    else:
                        # Resposta caso digite algo diferente de 1 ou 2
                        opcao_invalida = "Desculpe, não entendi. Digite apenas *1* para Pessoa Jurídica ou *2* para Pessoa Física. 👇"
                        responder_mensagem(numero, opcao_invalida)

                elif estado_atual == "dados_enviados":
                    # Deixa o fluxo livre para o cliente digitar os dados sem o bot responder
                    print(f"Cliente {numero} está digitando os dados solicitados.")

    except Exception as erro:
        print("ERRO AO PROCESSAR:")
        print(erro)

    return "ok", 200

def responder_mensagem(numero, mensagem):
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
