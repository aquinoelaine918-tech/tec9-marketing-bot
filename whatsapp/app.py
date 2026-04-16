from flask import Flask, request

app = Flask(__name__)

# =========================
# ROTA PRINCIPAL
# =========================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

# =========================
# HEALTH CHECK
# =========================
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# =========================
# WEBHOOK GET
# =========================
@app.route("/webhook", methods=["GET"])
def webhook_verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    return f"Webhook GET OK | mode={mode} | token={token} | challenge={challenge}", 200

# =========================
# WEBHOOK POST
# =========================
@app.route("/webhook", methods=["POST"])
def webhook_receive():
    data = request.get_json(silent=True)

    print("POST recebido no webhook:")
    print(data)

    return "ok", 200

# =========================
# INICIALIZAÇÃO LOCAL
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
