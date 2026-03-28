from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "tec9token123"

@app.route("/", methods=["GET"])
def home():
    return "Bot online", 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Erro de verificação", 403

    if request.method == "POST":
        return "ok", 200


# 🔥 ESSA PARTE É CRÍTICA
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
