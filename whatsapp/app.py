from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Configurações integradas com o painel de variáveis do seu Railway
VERIFY_TOKEN = "tec9token123"
WHATSAPP_TOKEN = os.getenv("EAAK409sUM3YBRYFqSVuTAVdObC87ZA2keusWA7pZCqFeqPoZA63iXuz5kZCZB3dMAZCVq6eiikWKX8TrCYXZCu8Bzcn4gyMBP0Huo9ZApwARBtZCY1oPe7RpvZA8sYzrJ89ZCGPvmGvXpoAEpiNpxrp5DqVrkVVHYvGp5zaV7mRKx4lVHuqP7sPqZCQcl9l8Gg0YRTJZBEgm7wvTNI0t4503ZAbgWwaL6m7osUTmfWBXmdvh7wtCZBGhYYIPobZCThVKaO7JEYxPLZCUyJ3yRRrSpZAkdCTs1ZCsOwgawZDZD")
PHONE_NUMBER_ID = os.getenv("1099079283287430")

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
        # Navegação segura na estrutura JSON da Meta
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # Ignora se for apenas uma notificação de status (enviado, entregue, lido)
        if "messages" not in value:
            return "ok", 200

        message = value["messages"][0]
        tipo = message.get("type")
        numero = message.get("from")

        print(f"TIPO: {tipo} DE: {numero}")

        # Proteção contra payloads de erro enviados pela própria Meta
        if "errors" in message:
            print(f"Erro recebido da Meta no webhook: {message['errors']}")
            return "ok", 200

        # Filtro estrito: ignora de forma segura áudios, imagens, figurinhas, reações, etc.
        if tipo != "text" or "text" not in message:
            print("Mensagem de tipo não suportado ignorada com sucesso.")
            return "ok", 200

        # Captura o texto enviado pelo cliente
        texto = message["text"].get("body", "").strip()

        print(f"MENSAGEM DE {numero}: {texto}")

        # Executa o envio da resposta automática
        enviar_mensagem(numero, f"Você disse: {texto}")
        return "ok", 200

    except Exception as erro:
        # Evita loops de reenvio da Meta salvando o erro no log e respondendo 200 OK
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
