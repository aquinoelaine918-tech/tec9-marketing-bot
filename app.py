from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# O Token de verificação que você deve colocar no painel da Meta
VERIFY_TOKEN = "tec9seguro123"

@app.route('/')
def home():
    return "Bot Online!", 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Lógica de verificação do Webhook para a Meta
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Erro de verificação", 403

    if request.method == 'POST':
        # Aqui o bot processa as mensagens recebidas
        data = request.get_json()
        print("Mensagem recebida:", data)
        return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    # O Railway fornece a porta automaticamente pela variável de ambiente PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
