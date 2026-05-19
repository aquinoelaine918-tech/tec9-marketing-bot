from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "TEC9_TOKEN"
WHATSAPP_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Dicionário temporário na memória para lembrar a etapa de cada cliente
# Nota: Como zera ao reiniciar o servidor, para produção futura recomenda-se um banco de dados
estados_clientes = {}

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

    try:
        entry = data.get("entry", [{}])
        changes = entry[0].get("changes", [{}])
        value = changes[0].get("value", {})

        if "messages" not in value:
            return "ok", 200

        message = value["messages"][0]
        tipo = message.get("type")
        numero = message.get("from")

        if "errors" in message or tipo != "text" or "text" not in message:
            return "ok", 200

        texto_cliente = message["text"].get("body", "").strip()

        # Verifica em qual etapa o cliente está
        estado_atual = estados_clientes.get(numero, "inicio")

        if estado_atual == "inicio":
            # Bloco 1: Menu Inicial de Boas-vindas
            menu_inicial = (
                "Olá, seja bem-vindo à TEC9 Informática 🚀\n\n"
                "Para iniciarmos seu atendimento, selecione uma opção:\n\n"
                "1️⃣ Pessoa Jurídica\n"
                "2️⃣ Pessoa Física\n\n"
                "Digite o número correspondente 👇"
            )
            enviar_mensagem(numero, menu_inicial)
            estados_clientes[numero] = "aguardando_opcao"

        elif estado_atual == "aguardando_opcao":
            if texto_cliente == "1":
                # Bloco 2: Resposta para Pessoa Jurídica
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
                enviar_mensagem(numero, resposta_pj)
                estados_clientes[numero] = "dados_enviados"

            elif texto_cliente == "2":
                # Bloco 3: Resposta para Pessoa Física
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
                enviar_mensagem(numero, resposta_pf)
                estados_clientes[numero] = "dados_enviados"

            else:
                # Caso digite qualquer outra coisa inválida no menu
                opcao_invalida = "Desculpe, não entendi. Digite apenas *1* para Pessoa Jurídica ou *2* para Pessoa Física. 👇"
                enviar_mensagem(numero, opcao_invalida)

        elif estado_atual == "dados_enviados":
            # Aqui o cliente já escolheu o fluxo e está digitando os dados dele.
            # O bot apenas lê, mas não interfere para deixar o humano assumir.
            print(f"Cliente {numero} enviando dados do orçamento: {texto_cliente}")

        return "ok", 200

    except Exception as erro:
        print(f"ERRO INTERNO EVITADO: {erro}")
        return "ok", 200

def enviar_mensagem(numero, mensagem):
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": mensagem}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"STATUS ENVIO: {response.status_code}")
    except Exception as e:
        print(f"Falha na requisição: {e}")

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=porta)

