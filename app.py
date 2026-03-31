from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Configurações das Variáveis de Ambiente do Railway
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Token inválido", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("Dados brutos recebidos:", data) # Para você ver nos logs

    try:
        # A estrutura da Meta é complexa: entry -> changes -> value -> messages
        if data.get('entry') and data['entry'][0].get('changes'):
            value = data['entry'][0]['changes'][0].get('value')
            
            if value and 'messages' in value:
                message = value['messages'][0]
                from_number = message['from']
                
                # Verifica se é uma mensagem de texto
                if message.get('type') == 'text':
                    text_received = message['text']['body'].lower().strip()
                    print(f"Mensagem de {from_number}: {text_received}")

                    # Lógica do Menu TEC9
                    if text_received in ["oi", "olá", "ola", "menu"]:
                        resposta = (
                            "Olá! Bem-vindo à *TEC9 Informática*! 💻\n\n"
                            "Como podemos ajudar?\n"
                            "1️⃣ - Suporte Técnico\n"
                            "2️⃣ - Orçamentos\n"
                            "3️⃣ - Falar com atendente"
                        )
                    elif text_received == "1":
                        resposta = "🔧 *Suporte:* Descreva seu problema e responderemos em breve."
                    elif text_received == "2":
                        resposta = "💰 *Orçamentos:* Acesse tec9informatica.com.br"
                    elif text_received == "3":
                        resposta = "👤 *Atendimento:* Aguarde um momento..."
                    else:
                        resposta = "Digite *OI* para ver o menu."

                    enviar_mensagem(from_number, resposta)

    except Exception as e:
        print(f"Erro ao processar: {e}")

    return "ok", 200

def enviar_mensagem(numero, texto_enviar):
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

if __name__ == "__main__":
    # Garante que o Railway não derrube o container
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
