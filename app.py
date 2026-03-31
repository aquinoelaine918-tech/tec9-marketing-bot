from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Configurações vindas das variáveis de ambiente do Railway
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# =========================
# VERIFICAÇÃO DO WEBHOOK
# =========================
@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Token inválido", 403

# =========================
# RECEBER E PROCESSAR MENSAGENS
# =========================
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # Log para monitorar no Railway
    print("Dados recebidos da Meta:", data)

    try:
        # Verifica se existe uma mensagem no JSON recebido
        if 'messages' in data['entry'][0]['changes'][0]['value']:
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
            from_number = message['from']
            text_received = message['text']['body'].lower().strip()

            print(f"Mensagem de {from_number}: {text_received}")

            # Lógica do Menu TEC9
            if text_received in ["oi", "olá", "ola", "menu"]:
                resposta = (
                    "Olá! Bem-vindo à *TEC9 Informática*! 💻\n\n"
                    "Como podemos ajudar hoje?\n"
                    "1️⃣ - Suporte Técnico\n"
                    "2️⃣ - Orçamentos\n"
                    "3️⃣ - Falar com atendente"
                )
            elif text_received == "1":
                resposta = "🔧 *Suporte Técnico:* Por favor, descreva o problema e um técnico da TEC9 responderá em breve."
            elif text_received == "2":
                resposta = "💰 *Orçamentos:* Acesse tec9informatica.com.br ou mande os itens aqui para cotação."
            elif text_received == "3":
                resposta = "👤 *Atendimento:* Aguarde um momento, um de nossos atendentes já vai falar com você."
            else:
                resposta = "Ainda não entendi... 🤔\nDigite *OI* para ver as opções do nosso menu."

            enviar_mensagem(from_number, resposta)

    except Exception as e:
        print("Erro ao processar:", e)

    return "ok", 200

# =========================
# FUNÇÃO PARA ENVIAR WHATSAPP
# =========================
def enviar_mensagem(numero, texto_enviar):
    # Versão atualizada v20.0
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto_enviar}
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    print("Resposta da Meta:", response.text)

# =========================
# INICIALIZAÇÃO DO SERVIDOR
# =========================
if __name__ == "__main__":
    # O Railway exige que o app rode na porta definida pela variável PORT
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
