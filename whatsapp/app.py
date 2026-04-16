import os
import json
import traceback
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ===== VARIÁVEIS =====
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")

# ===== CONFIG TESTE TEMPLATE =====
TEST_TO_NUMBER = os.getenv("TEST_TO_NUMBER", "5511952686414")
TEST_TEMPLATE_NAME = os.getenv("TEST_TEMPLATE_NAME", "hello_world")
TEST_TEMPLATE_LANG = os.getenv("TEST_TEMPLATE_LANG", "pt_BR")

# ===== HEADERS =====
def meta_headers():
    return {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

# ===== HOME =====
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀"

# ===== HEALTH =====
@app.route("/health", methods=["GET"])
def health():
    return "OK"

# ===== VERIFICAÇÃO WEBHOOK =====
@app.route("/webhook", methods=["GET"])
def verify():
    try:
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Erro de verificação", 403

    except Exception as e:
        print("Erro verify:", e)
        return "Erro", 500

# ===== RECEBER MENSAGEM =====
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        print("Payload recebido:", json.dumps(data, indent=2))

        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]
            numero = message["from"]

            if "text" in message:
                texto = message["text"]["body"]
            else:
                texto = "Mensagem não suportada"

            print(f"Mensagem de {numero}: {texto}")

            resposta = gerar_resposta(texto)
            enviar_texto(numero, resposta)

    except Exception as e:
        print("Erro webhook:")
        traceback.print_exc()

    return "ok", 200

# ===== IA (RESPOSTA SIMPLES POR ENQUANTO) =====
def gerar_resposta(texto):
    return f"Recebi sua mensagem: {texto}\n\nEquipe TEC9 já vai te atender 😉"

# ===== ENVIO TEXTO =====
def enviar_texto(numero, texto):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": texto
        }
    }

    response = requests.post(url, headers=meta_headers(), json=payload)
    print("Envio texto:", response.status_code, response.text)

# ===== ENVIO TEMPLATE TESTE =====
@app.route("/teste", methods=["GET"])
def teste_template():
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": TEST_TO_NUMBER,
        "type": "template",
        "template": {
            "name": TEST_TEMPLATE_NAME,
            "language": {
                "code": TEST_TEMPLATE_LANG
            }
        }
    }

    response = requests.post(url, headers=meta_headers(), json=payload)

    return jsonify({
        "status": response.status_code,
        "resposta": response.text
    })

# ===== RODAR =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
