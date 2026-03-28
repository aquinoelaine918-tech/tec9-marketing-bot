import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

@app.route("/", methods=["GET"])
def home():
    return "BOT TEC9 ONLINE 🚀", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Erro verificação", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()
    print("Mensagem recebida:", data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]
            from_number = message["from"]

            texto = ""
            if message["type"] == "text":
                texto = message["text"]["body"]

            resposta = gerar_resposta(texto)
            enviar_mensagem(from_number, resposta)

    except Exception as e:
        print("Erro:", str(e))

    return jsonify({"status": "ok"}), 200

def gerar_resposta(texto):
    texto = (texto or "").lower()

    if "ssd" in texto:
        return "Temos SSD disponível 👍 Me informe a capacidade (240GB, 480GB ou 1TB) que te envio o link."

    if "notebook" in texto:
        return "Temos notebooks profissionais. Me informe seu orçamento que te envio opções com link."

    if "preço" in texto or "valor" in texto:
        return "Claro 👍 Me informe o produto que você procura que te envio preço e link de compra."

    if "entrega" in texto or "prazo" in texto:
        return "Me informe seu CEP e o produto para eu verificar o prazo de entrega."

    return "Olá! 👋 Bem-vindo à TEC9 Informática. Me diga o produto que você procura que te envio as melhores opções com link de compra."

def enviar_mensagem(numero, mensagem):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": mensagem}
    }

    response = requests.post(url, headers=headers, json=payload)
    print("Resposta:", response.status_code, response.text)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
