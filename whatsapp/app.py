import os
import json
import traceback
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")

TEST_TO_NUMBER = os.getenv("TEST_TO_NUMBER", "5511952686414")
TEST_TEMPLATE_NAME = os.getenv("TEST_TEMPLATE_NAME", "teste_tec9")
TEST_TEMPLATE_LANG = os.getenv("TEST_TEMPLATE_LANG", "pt_BR")


def meta_headers():
    return {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def safe_json_or_text(response_text: str):
    try:
        return json.loads(response_text)
    except Exception:
        return response_text


def send_template_message(to_number: str):
    if not META_ACCESS_TOKEN:
        raise ValueError("META_ACCESS_TOKEN não configurado.")
    if not PHONE_NUMBER_ID:
        raise ValueError("PHONE_NUMBER_ID não configurado.")
    if not to_number:
        raise ValueError("Número de destino não informado.")

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": TEST_TEMPLATE_NAME,
            "language": {
                "code": TEST_TEMPLATE_LANG
            }
        }
    }

    response = requests.post(url, headers=meta_headers(), json=payload, timeout=30)
    return response.status_code, response.text


@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "verify_token_configurado": bool(VERIFY_TOKEN),
        "meta_access_token_configurado": bool(META_ACCESS_TOKEN),
        "phone_number_id_configurado": bool(PHONE_NUMBER_ID),
        "phone_number_id": PHONE_NUMBER_ID,
        "test_template_name": TEST_TEMPLATE_NAME,
        "test_template_lang": TEST_TEMPLATE_LANG,
        "test_to_number": TEST_TO_NUMBER
    }), 200


@app.route("/send", methods=["GET"])
def send_test():
    try:
        to_number = request.args.get("to", TEST_TO_NUMBER).strip()
        status_code, response_text = send_template_message(to_number)

        return jsonify({
            "ok": 200 <= status_code < 300,
            "sent_to": to_number,
            "status_code": status_code,
            "response": safe_json_or_text(response_text)
        }), status_code

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    try:
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200

        return "Token de verificação inválido", 403

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route("/webhook", methods=["POST"])
def receive_webhook():
    try:
        data = request.get_json(silent=True) or {}

        print("WEBHOOK RECEBIDO:")
        print(json.dumps(data, ensure_ascii=False, indent=2))

        return jsonify({"status": "received"}), 200

    except Exception as e:
        print("ERRO NO WEBHOOK:")
        print(traceback.format_exc())
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
