@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # O Facebook envia estes parâmetros para validar seu servidor
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        # O 'token' deve ser exatamente o que você digitou no painel da Meta
        if mode == "subscribe" and token == "tec9_webhook_2026":
            return challenge, 200 # DEVE retornar apenas o valor do challenge
        return "Token inválido", 403
    
    # Aqui entra sua lógica para processar mensagens (POST)
    return "OK", 200
