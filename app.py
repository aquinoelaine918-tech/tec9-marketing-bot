import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIÁVEIS (Railway)
# =========================
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


# =========================
# TESTE ONLINE
# =========================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


# =========================
# WEBHOOK (META)
# =========================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # ===== VERIFICAÇÃO META =====
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Erro de verificação", 403

    # ===== RECEBER EVENTOS =====
    if request.method == "POST":
        data = request.get_json(silent=True)

        print("Webhook recebido:", data, flush=True)

        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]

            if "messages" in value:
                message = value["messages"][0]
                numero = message["from"]

                tipo = message.get("type")

                if tipo == "text":
                    texto = message["text"]["body"]
                else:
                    texto = f"Tipo recebido: {tipo}"

                print("Mensagem:", texto, flush=True)

                responder(numero, texto)

        except Exception as e:
            print("Erro:", e, flush=True)

        return jsonify({"status": "ok"}), 200


# =========================
# ENVIAR RESPOSTA
# =========================
def responder(numero, texto_recebido):

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    mensagem = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": f"Olá! 👋\n\nRecebi sua mensagem:\n👉 {texto_recebido}\n\nComo posso te ajudar hoje?"
        }
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=mensagem, headers=headers)

    print("Resposta enviada:", response.text, flush=True)


# =========================
# RAILWAY PORTA DINÂMICA
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
