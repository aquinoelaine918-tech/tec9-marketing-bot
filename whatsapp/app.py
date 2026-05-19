from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Configurações estritamente validadas do seu painel Meta
VERIFY_TOKEN = "TEC9_TOKEN"
WHATSAPP_TOKEN = "EAAK409sUM3YBRVp9nT4Dr72el46ZCHvgVvnKowN1qBJKti5gD1ixN5MNfX8D6t5iB8FWd6LAasxstr8jNseqBBEoH"
PHONE_NUMBER_ID = "1099079283287430"

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
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # Ignora notificações de leitura ou entrega
        if "messages" not in value:
            return "ok", 200

        message = value["messages"][0]
        tipo = message.get("type")
        numero = message.get("from")

        print(f"TIPO: {tipo} DE: {numero}")

        # Ignora payloads de erro enviados pela própria API da Meta
        if "errors" in message:
            print(f"Erro recebido da Meta: {message['errors']}")
            return "ok", 200

        # Ignora com segurança áudios, imagens, figurinhas e reações
        if tipo != "text" or "text" not in message:
            print("Mensagem de tipo não suportado ignorada com sucesso.")
            return "ok", 200

        texto = message["text"].get("body", "").strip()

        print(f"MENSAGEM DE {numero}: {texto}")

        # Executa o envio da resposta
        enviar_mensagem(numero, f"Você disse: {texto}")
        return "ok", 200

    except Exception as erro:
        # Registra a falha internamente, mas retorna 200 para evitar loops de reenvio da Meta
        print(f"ERRO INTERNO EVITADO: {erro}")
        return "ok", 200

def enviar_mensagem(numero, mensagem):
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
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Envio: {response.status_code}")
        print(f"Resposta Envio: {response.text}")
    except Exception as e:
        print(f"Falha na requisição HTTP de envio: {e}")

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=porta)
