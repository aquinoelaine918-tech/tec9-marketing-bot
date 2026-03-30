from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 🔥 TOKEN FIXO (IMPORTANTE PARA TESTE)
VERIFY_TOKEN = "tec9token123"

# 🔐 VEM DO RAILWAY
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


# 🔹 ROTA PRINCIPAL
@app.route("/", methods=["GET"])
def home():
    return "Bot online", 200


# 🔹 TESTE DE VERIFICAÇÃO (MOSTRA O ERRO REAL)
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    return {
        "token_recebido": repr(token),
        "verify_token_app": repr(VERIFY_TOKEN),
        "iguais": token == VERIFY_TOKEN,
        "challenge": challenge
    }, 200


# 🔹 RECEBER MENSAGENS
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Recebido:", data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]
            from_number = message["from"]
            texto = message["text"]["body"]

            resposta = f"Olá! 👋 Recebi sua mensagem: {texto}\n\nSou a TEC9 Informática e vou te ajudar agora."

            url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

            headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": "text",
                "text": {"body": resposta}
            }

            r = requests.post(url, headers=headers, json=payload)
            print(r.status_code, r.text)

    except Exception as e:
        print("Erro:", e)

    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
