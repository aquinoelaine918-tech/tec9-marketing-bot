import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = (os.getenv("VERIFY_TOKEN") or "").strip()
ACCESS_TOKEN = (os.getenv("META_ACCESS_TOKEN") or "").strip()
PHONE_NUMBER_ID = (os.getenv("PHONE_NUMBER_ID") or "").strip()


@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE", 200


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

    data = request.get_json(silent=True)
    print("WEBHOOK RECEBIDO:", data, flush=True)

    try:
        if not data:
            return jsonify({"status": "no data"}), 200

        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                if "messages" not in value:
                    continue

                for message in value.get("messages", []):
                    from_number = message.get("from")
                    message_type = message.get("type")

                    if not from_number:
                        continue

                    if message_type == "text":
                        text_body = message.get("text", {}).get("body", "")
                    else:
                        text_body = f"Mensagem recebida do tipo: {message_type}"

                    print(f"MENSAGEM RECEBIDA DE {from_number}: {text_body}", flush=True)

                    responder_mensagem(
                        from_number,
                        f"Olá! 👋\n\nRecebi sua mensagem:\n👉 {text_body}\n\nEm breve um especialista TEC9 vai te atender 🚀"
                    )

    except Exception as e:
        print("ERRO AO PROCESSAR WEBHOOK:", str(e), flush=True)

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
        print("RESPOSTA ENVIADA:", response.status_code, response.text, flush=True)
    except Exception as e:
        print("ERRO AO ENVIAR RESPOSTA:", str(e), flush=True)
