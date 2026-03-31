import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configurações do Railway (Variáveis de Ambiente)
VERIFY_TOKEN = (os.getenv("VERIFY_TOKEN") or "").strip()
ACCESS_TOKEN = (os.getenv("META_ACCESS_TOKEN") or "").strip()
PHONE_NUMBER_ID = (os.getenv("PHONE_NUMBER_ID") or "").strip()

@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # 1. VERIFICAÇÃO DO FACEBOOK (GET)
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge, 200
        return "Erro de verificacao", 403

    # 2. RECEBIMENTO DE MENSAGENS (POST)
    data = request.get_json(silent=True)
    
    try:
        if not data or 'entry' not in data:
            return jsonify({"status": "sem dados"}), 200

        for entry in data['entry']:
            for change in entry.get('changes', []):
                value = change.get('value', {})

                # --- FILTRO IMPORTANTE: IGNORA STATUS (ENTREGA, LEITURA) ---
                if "statuses" in value:
                    print("Status de leitura/entrega ignorado.", flush=True)
                    continue

                # --- FILTRO IMPORTANTE: PROCESSA SOMENTE MENSAGENS REAIS ---
                if "messages" not in value:
                    continue

                for message in value.get('messages', []):
                    from_number = message.get('from')
                    
                    # Verifica se é uma mensagem de texto
                    if message.get('type') == 'text':
                        texto = message['text']['body'].lower().strip()
                        print(f"MENSAGEM DE {from_number}: {texto}", flush=True)

                        # ==========================================
                        # LÓGICA DE ATENDIMENTO TEC9
                        # ==========================================
                        
                        # A. Busca por Preços/Valores
                        if any(p in texto for p in ["preço", "valor", "quanto", "custa", "orcamento", "orçamento"]):
                            resposta = (
                                "Perfeito! 🔥\n\n"
                                "Para te passar o melhor preço agora, preciso de:\n\n"
                                "• Produto ou modelo\n"
                                "• Quantidade\n"
                                "• Cidade de entrega\n\n"
                                "👉 Vou verificar estoque e condição especial pra você!"
                            )
                        
                        # B. Saudação Inicial e Menu
                        elif any(p in texto for p in ["oi", "olá", "ola", "menu", "bom dia", "boa tarde"]):
                            resposta = (
                                "Olá! 👋 Bem-vindo à *TEC9 Informática*! 💻\n\n"
                                "Como podemos ajudar hoje?\n\n"
                                "1️⃣ - Suporte Técnico 🛠️\n"
                                "2️⃣ - Orçamentos / Vendas 💰\n"
                                "3️⃣ - Falar com Especialista 👤\n\n"
                                "👉 Digite apenas o *número* da opção."
                            )

                        # C. Opções Numéricas
                        elif texto == "1":
                            resposta = "🔧 *Suporte:* Por favor, descreva o defeito do seu equipamento. Um técnico da TEC9 analisará em breve!"
                        elif texto == "2":
                            resposta = "💰 *Orçamentos:* Ótima escolha! Acesse *tec9informatica.com.br* ou mande a lista aqui."
                        elif texto == "3":
                            resposta = "👤 *Especialista:* Aguarde um momento. Estamos transferindo para um atendimento humano..."
                        
                        # D. Resposta Padrão para o que não entender
                        else:
                            resposta = "Ops! Não entendi. 🤔\nDigite *OI* para ver as opções ou pergunte o *VALOR* de um produto."

                        enviar_mensagem(from_number, resposta)

    except Exception as e:
        print(f"ERRO NO WEBHOOK: {e}", flush=True)

    return jsonify({"status": "received"}), 200

def enviar_mensagem(numero, texto):
    # Versão v22.0 (A mais atual da Meta)
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"
    
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
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        print(f"RESPOSTA ENVIADA: {response.status_code}", flush=True)
    except Exception as e:
        print(f"ERRO AO ENVIAR: {e}", flush=True)

if __name__ == "__main__":
    # Configuração de porta para o Railway
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
