import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# ==========================================
# CONFIGURAÇÕES (VARIÁVEIS DE AMBIENTE)
# ==========================================
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "123456")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ==========================================
# ROTAS DE TESTE E SAÚDE
# ==========================================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "openai": "configurada" if OPENAI_API_KEY else "pendente",
        "meta_token": "configurado" if META_ACCESS_TOKEN else "pendente",
        "phone_number_id": "configurado" if PHONE_NUMBER_ID else "pendente"
    }), 200


# ==========================================
# WEBHOOK: VERIFICAÇÃO (META)
# ==========================================
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return challenge, 200

    return "Erro de verificação", 403


# ==========================================
# WEBHOOK: RECEBER MENSAGENS
# ==========================================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)

    print("Webhook recebido:")
    print(data)

    try:
        if not data:
            return "EVENT_RECEIVED", 200

        if (
            data.get("entry")
            and data["entry"][0].get("changes")
            and data["entry"][0]["changes"][0].get("value")
            and "messages" in data["entry"][0]["changes"][0]["value"]
        ):
            value = data["entry"][0]["changes"][0]["value"]
            messages = value.get("messages", [])

            if not messages:
                return "EVENT_RECEIVED", 200

            message = messages[0]
            from_number = message.get("from")

            if not from_number:
                return "EVENT_RECEIVED", 200

            # Evita processar tipos que não sejam texto
            if message.get("type") == "text" and "text" in message:
                user_text = message["text"].get("body", "").strip()

                if not user_text:
                    return "EVENT_RECEIVED", 200

                print(f"Mensagem de {from_number}: {user_text}")

                # 1. Gera a resposta com IA
                resposta_ia = gerar_resposta(user_text)

                # 2. Envia resposta ao WhatsApp
                envio_ok = enviar_mensagem(from_number, resposta_ia)

                if envio_ok:
                    print(f"Resposta enviada com sucesso para {from_number}")
                else:
                    print(f"Falha ao enviar resposta para {from_number}")

    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")

    return "EVENT_RECEIVED", 200


# ==========================================
# FUNÇÃO: RESPOSTA IA (OPENAI)
# ==========================================
def gerar_resposta(pergunta: str) -> str:
    try:
        if not OPENAI_API_KEY:
            print("OPENAI_API_KEY não configurada.")
            return (
                "Olá! Sou o assistente da TEC9 Informática. "
                "Recebi sua mensagem e em breve vou te ajudar da melhor forma possível."
            )

        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um vendedor especialista da TEC9 Informática. "
                        "Seja profissional, objetivo, cordial e foque em ajudar o cliente "
                        "a comprar produtos de informática. Quando faltar informação, "
                        "faça perguntas curtas para entender melhor a necessidade."
                    )
                },
                {
                    "role": "user",
                    "content": pergunta
                }
            ],
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Erro OpenAI: {e}")
        return (
            "Olá! Sou o assistente da TEC9 Informática. "
            "No momento tive uma instabilidade, mas posso continuar te ajudando. "
            "Me diga qual produto você procura."
        )


# ==========================================
# FUNÇÃO: ENVIO DE MENSAGEM (META API)
# ==========================================
def enviar_mensagem(numero: str, texto: str) -> bool:
    try:
        if not META_ACCESS_TOKEN:
            print("META_ACCESS_TOKEN não configurado.")
            return False

        if not PHONE_NUMBER_ID:
            print("PHONE_NUMBER_ID não configurado.")
            return False

        url = f"https://graph.facebook.com/v23.0/{PHONE_NUMBER_ID}/messages"

        headers = {
            "Authorization": f"Bearer {META_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": texto
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"Status do envio para {numero}: {response.status_code}")
        print(f"Resposta da Meta: {response.text}")

        return response.status_code in (200, 201)

    except Exception as e:
        print(f"Erro ao enviar para WhatsApp: {e}")
        return False


# ==========================================
# INICIALIZAÇÃO DO SERVIDOR
# ==========================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
