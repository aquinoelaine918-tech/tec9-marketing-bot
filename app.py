from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# CONFIGURAÇÕES FIXAS (Para não dar erro de verificação)
VERIFY_TOKEN = "tec9token123" 
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

@app.route("/", methods=["GET"])
def home():
    return "Bot TEC9 Online!", 200

@app.route("/webhook", methods=["GET"])
def verify():
    # O Facebook envia estes parâmetros para validar seu bot
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    # Verifica se o token enviado pelo Facebook é igual ao que definimos acima
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK_VERIFICADO")
        return challenge, 200
    
    print("ERRO DE VERIFICAÇÃO: Token incorreto")
    return "Erro de verificação", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Mensagem Recebida:", data)

    try:
        if "messages" in data["entry"][0]["changes"][0]["value"]:
            value = data["entry"][0]["changes"][0]["value"]
            message = value["messages"][0]
            from_number = message["from"]

            # Captura o texto da mensagem
            texto_usuario = "mensagem recebida"
            if "text" in message:
                texto_usuario = message["body"]

            # Monta a resposta automática
            resposta_texto = f"Olá! 👋 Recebi sua mensagem: {texto_usuario}\n\nSou a TEC9 Informática e vou te ajudar agora."

            # URL da API do WhatsApp
            url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"

            headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": "text",
                "text": {"body": resposta_texto}
            }

            # Envia a resposta de volta para o usuário
            envio = requests.post(url, headers=headers, json=payload)
            print(f"Status do Envio: {envio.status_code}")

    except Exception as e:
        print(f"Erro ao processar mensagem: {str(e)}")

    return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    # O Railway define a porta automaticamente na variável PORT
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
