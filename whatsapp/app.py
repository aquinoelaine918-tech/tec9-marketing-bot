import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configurações extraídas do seu código original
VERIFY_TOKEN = "tec9token123"
WHATSAPP_TOKEN = "EAAK4D9sUM3YBROKk2A5ThSTAknCQzdMeazIFpFQDTxD2CZBJCZ8mQyonDdj jNteEjrhy03HkarF8KdLd7cuE3t3NkxzYmYq90wrP2YibRpKZArbZAUPQ0veuduZCmrNlqGFu4t5ZAqy0g"
PHONE_NUMBER_ID = "109907928287430"

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "TEC9 BOT ONLINE 🚀"
    }), 200

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
    return "Erro de verificação", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    print("Evento recebido:")
    print(data)

    try:
        # Validação segura da estrutura de dados do Meta
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # Ignora se for apenas alteração de status de leitura/entrega
        if "messages" not in value:
            return "ok", 200

        message = value["messages"][0]
        tipo = message.get("type")
        numero = message.get("from")

        print(f"Tipo recebido: {tipo} de {numero}")

        # Se houver erros no payload enviados pelo Meta, ignora e responde 200
        if "errors" in message:
            print(f"Erro detectado no payload do WhatsApp: {message['errors']}")
            return "ok", 200

        # Bloqueia de forma segura qualquer tipo que não seja texto
        if tipo != "text" or "text" not in message:
            print(f"Mensagem do tipo '{tipo}' ignorada com segurança.")
            return "ok", 200

        # Captura o texto enviado pelo cliente
        texto = message["text"].get("body", "").strip()
        print(f"Mensagem de {numero}: {texto}")

        # Envia a resposta automática
        responder_mensagem(numero, f"Você disse: {texto}")
        return "ok", 200

    except Exception as e:
        # Evita travar o bot em loop; loga o erro internamente e responde OK para o Meta
        print(f"ERRO INTERNO EVITADO: {e}")
        return "ok", 200

def responder_mensagem(numero, texto):
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
            "body": texto
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Envio: {response.status_code}")
        print(f"Resposta Envio: {response.text}")
    except Exception as e:
        print(f"Falha ao tentar enviar requisição POST: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
