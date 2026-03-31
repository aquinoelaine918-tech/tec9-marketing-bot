import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Pegando as variáveis do Railway
VERIFY_TOKEN = (os.getenv("VERIFY_TOKEN") or "").strip()
ACCESS_TOKEN = (os.getenv("META_ACCESS_TOKEN") or "").strip()
PHONE_NUMBER_ID = (os.getenv("PHONE_NUMBER_ID") or "").strip()

@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # Verificação do Facebook
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge, 200
        return "Erro de verificacao", 403

    # Recebimento de Mensagens
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
                    if not from_number: continue

                    # Pega o texto enviado pelo cliente
                    text_body = message.get("text", {}).get("body", "").lower().strip()
                    print(f"MENSAGEM DE {from_number}: {text_body}", flush=True)

                    # ==========================================
                    # LÓGICA DO MENU TEC9 INFORMÁTICA
                    # ==========================================
                    if text_body in ["oi", "olá", "ola", "menu", "bom dia", "boa tarde"]:
                        resposta = (
                            "Olá! 👋 Bem-vindo à *TEC9 Informática*! 💻\n\n"
                            "Como podemos ajudar você hoje?\n\n"
                            "1️⃣ - Suporte Técnico 🛠️\n"
                            "2️⃣ - Orçamentos / Vendas 💰\n"
                            "3️⃣ - Falar com Especialista 👤\n\n"
                            "👉 Digite apenas o *número* da opção desejada."
                        )
                    elif text_body == "1":
                        resposta = "🔧 *Suporte Técnico:* Por favor, descreva o defeito do seu equipamento. Um técnico da TEC9 analisará em breve!"
                    elif text_body == "2":
                        resposta = "💰 *Orçamentos:* Ótima escolha! Acesse nosso site *tec9informatica.com.br* ou mande a lista de itens aqui."
                    elif text_body == "3":
                        resposta = "👤 *Especialista:* Aguarde um momento. Estamos transferindo você para um atendimento humano..."
                    else:
                        resposta = "Ops! Não entendi. 🤔\nDigite *OI* para ver nosso menu de opções."

                    responder_mensagem(from_number, resposta)

    except Exception as e:
        print("ERRO AO PROCESSAR WEBHOOK:", str(e), flush=True)

    return jsonify({"status": "received"}), 200

def responder_mensagem(numero, texto):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print("RESPOSTA ENVIADA:", response.status_code, flush=True)
    except Exception as e:
        print("ERRO AO ENVIAR:", str(e), flush=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
