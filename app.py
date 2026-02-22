from flask import Flask, request, jsonify

app = Flask(__name__)

# Rota principal (teste)
@app.get("/")
def home():
    return "Tec9 bot rodando no Render ✅"

# Webhook do Verdent / Instagram
@app.post("/webhook")
def webhook():
    data = request.get_json(silent=True) or {}

    print("Mensagem recebida:", data)

    # Resposta simples (teste)
    return jsonify({
        "reply": "Olá 👋 Recebi sua mensagem pelo Instagram!"
    })

if __name__ == "__main__":
    app.run()
