import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "tec9token123")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


@app.route("/", methods=["GET"])
def home():
    return "Bot online", 200


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge, 200
        return "Erro de verificacao", 403

    if request.method == "POST":
        data = request.get_json(silent=True)
        print("Webhook recebido:", data, flush=True)

        try:
            if not data:
                return jsonify({"status": "no data"}), 200

            entry = data.get("entry", [])
            if not entry:
                return jsonify({"status": "no entry"}), 200

            changes = entry[0].get("changes", [])
            if not changes:
                return jsonify({"status": "no changes"}), 200

            value = changes[0].get("value", {})

            if "messages" in value:
                message = value["messages"][0]
                from_number = message.get("from")

                message_type = message.get("type")
                text_body = ""

                if message_type == "text":
                    text_body = message.get("text", {}).get("body", "")
                else:
                    text_body = f"Mensagem recebida do tipo: {message_type}"

                print("Mensagem recebida de", from_number, ":", text_body, flush=True)

                if from_number:
                    responder_mensagem(from_number, f"Recebi sua mensagem: {text_body}")

        except Exception as e:
            print("Erro ao processar webhook:", str(e), flush=True)

        return jsonify({"status": "received"}), 200


def responder_mensagem(numero, texto):
    if not ACCESS_TOKEN:
        print("META_ACCESS_TOKEN nao configurado", flush=True)
        return

    if not PHONE_NUMBER_ID:
        print("PHONE_NUMBER_ID nao configurado", flush=True)
        return

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": texto
        }
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print("Resposta enviada:", response.status_code, response.text, flush=True)
    except Exception as e:
        print("Erro ao enviar resposta:", str(e), flush=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
