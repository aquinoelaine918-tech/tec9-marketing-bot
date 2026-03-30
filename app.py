from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# =========================
# CONFIGURAÇÕES
# =========================

VERIFY_TOKEN = "tec9token123"

ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# =========================
# ROTA TESTE
# =========================

@app.route("/", methods=["GET"])
def home():
    return "Bot online", 200

# =========================
# VERIFICAÇÃO DO WEBHOOK (META)
# =========================

@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print("TOKEN RECEBIDO:", token)
    print("TOKEN ESPERADO:", VERIFY_TOKEN)

    if token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Erro de verificação", 403

# =========================
# RECEBER MENSAGENS DO WHATSAPP
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    print("DADOS RECEBIDOS:", data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]
            phone = message["from"]

            if message["type"] == "text":
                text = message["text"]["body"]

                print("Mensagem recebida:", text)

                resposta = f"Olá! Recebi sua mensagem: {text}"

                enviar_mensagem(phone, resposta)

    except Exception as e:
        print("Erro ao processar:", e)

    return "ok", 200

# =========================
# ENVIAR MENSAGEM
# =========================

def enviar_mensagem(phone, texto):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": texto}
    }

    response = requests.post(url, headers=headers, json=payload)

    print("Resposta envio:", response.text)

# =========================
# EXECUÇÃO
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
