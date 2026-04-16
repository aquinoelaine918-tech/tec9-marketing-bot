import os
import json
import traceback
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ========================
# VARIÁVEIS DE AMBIENTE
# ========================
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

TEST_TO_NUMBER = os.getenv("TEST_TO_NUMBER", "5511952686414")
TEST_TEMPLATE_NAME = os.getenv("TEST_TEMPLATE_NAME", "teste_tec9")
TEST_TEMPLATE_LANG = os.getenv("TEST_TEMPLATE_LANG", "pt_BR")


# ========================
# FUNÇÕES AUXILIARES
# ========================
def headers():
    return {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }


def send_template(to):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": TEST_TEMPLATE_NAME,
            "language": {
                "code": TEST_TEMPLATE_LANG
            }
        }
    }

    response = requests.post(url, headers=headers(), json=payload)

    return response.status_code, response.text


# ========================
# ROTAS
# ========================

@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "meta_access_token": bool(META_ACCESS_TOKEN),
        "phone_number_id": PHONE_NUMBER_ID,
        "template": TEST_TEMPLATE_NAME,
        "numero_teste": TEST_TO_NUMBER
    })


@app.route("/send", methods=["GET"])
def send():
    try:
        numero = request.args.get("to", TEST_TO_NUMBER)

        status, resposta = send_template(numero)

        return jsonify({
            "status_code": status,
            "response": resposta
        })

    except Exception as e:
        return jsonify({
            "erro": str(e),
            "trace": traceback.format_exc()
        }), 500


# ========================
# WEBHOOK META
# ========================

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Erro de verificação", 403


@app.route("/webhook", methods=["POST"])
def receive():
    data = request.get_json()

    print("Mensagem recebida:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    return "ok", 200


# ========================
# EXECUÇÃO
# ========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
