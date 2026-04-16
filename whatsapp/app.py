import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# ===== CONFIG =====
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

# ===== VERIFICAÇÃO DO WEBHOOK =====
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Erro de verificação", 403

# ===== RECEBER MENSAGEM =====
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    # O WhatsApp envia notificações de status (enviado, lido); ignoramos para evitar loops
    if not data or "entry" not in data:
        return jsonify({"status": "no data"}), 404

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]
            from_number = message["from"]
            
            # Verifica se a mensagem tem texto (evita erro com imagens/áudios por enquanto)
            if "text" in message:
                text = message["text"]["body"]
                print(f"Mensagem de {from_number}: {text}")

                resposta = gerar_resposta(text)
                enviar_mensagem(from_number, resposta)
            else:
                print("Mensagem recebida não contém texto.")

    except Exception as e:
        print(f"Erro no processamento: {e}")

    return jsonify({"status": "ok"}), 200

# ===== IA =====
def gerar_resposta(pergunta):
    try:
        # Ajustado de 'gpt-4.1-mini' (inexistente) para 'gpt-4o-mini'
        resposta = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": "Você é um vendedor especialista da TEC9 informática. Seja profissional, objetivo e ajude a vender."},
                {"role": "user", "content": pergunta}
            ]
        )
        return resposta.choices[0].message.content
    except Exception as e:
        print(f"Erro OpenAI: {e}")
        return "Desculpe, tive um problema técnico. Pode repetir a sua dúvida?"

# ===== ENVIO WHATSAPP =====
def enviar_mensagem(numero, texto):
    # Versão da API Meta atualizada para v21.0 (ou use a que preferir)
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Lança erro se o status for 4xx ou 5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar WhatsApp: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

