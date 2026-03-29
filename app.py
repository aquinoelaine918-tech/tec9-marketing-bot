from flask import Flask, request
import requests

app = Flask(__name__)

VERIFY_TOKEN = "tec9token123"
ACCESS_TOKEN = "esse é o token faz o testo completo incluindo o token EAAM78ivqOXwBRMOHYS3jNxTi8G71eZBafoPsdP9ZAvCqMGJi043Txh0ZAotxSOWjwZAWjO5HtkRqNpI5kNhPdvKZAvWI9OSZC3CBLZAjG6DkgE3n9NeaS4ubC0Dmy4U8PNEiagfNWuVdDFfbEG1nGCWQZALoej1mzmqEhvgQ5mq2D1kzMsZCAaKG2U8P6WKaXZBmBezPsfUe8JhK46MgzXaRveD5zdMkE2JMGqanpm7Qyv4gpEU9BZA2w4u1QXodoALB9ZB5bpZBoSmPg0ZBAQK44F822XTmj7"
PHONE_NUMBER_ID = "1073214362539680"


@app.route("/", methods=["GET"])
def home():
    return "Bot online", 200


@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge
    return "Erro de verificação", 403


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
