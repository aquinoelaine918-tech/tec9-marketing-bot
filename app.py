from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# =========================
# VERIFICAÇÃO DO WEBHOOK
# =========================
@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Token inválido", 403


# =========================
# RECEBER MENSAGENS
# =========================
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    print("Webhook recebido:", data)

    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']

        if 'messages' in value:
            message = value['messages'][0]
            from_number = message['from']
            text = message['text']['body']

            print("Mensagem recebida:", text)

            responder(from_number, text)

    except Exception as e:
        print("Erro:", e)

    return "ok", 200


# =========================
# FUNÇÃO DE RESPOSTA
# =========================
def responder(numero, texto_recebido):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    mensagem = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": f"Recebi sua mensagem: {texto_recebido}"
        }
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=mensagem, headers=headers)

    print("Resposta enviada:", response.text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
