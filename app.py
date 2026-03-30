from flask import Flask, request
import requests
import os

app = Flask(__name__)

# temporário: não vamos comparar token agora
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


@app.route("/", methods=["GET"])
def home():
    return "Bot online", 200


@app.route("/webhook", methods=["GET"])
def verify():
    challenge = request.args.get("hub.challenge")
    if challenge:
        return challenge, 200
    return "sem challenge", 200


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

            texto = "mensagem recebida"
            if "text" in message:
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
            print("META STATUS:", r.status_code)
            print("META RESPOSTA:", r.text)

    except Exception as e:
        print("Erro no POST /webhook:", str(e))

    return "ok", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
