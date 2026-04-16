from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "message": "TEC9 BOT ONLINE"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

@app.route("/webhook", methods=["GET"])
def webhook_verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    return jsonify({
        "mode": mode,
        "token": token,
        "challenge": challenge,
        "status": "webhook get ok"
    }), 200

@app.route("/webhook", methods=["POST"])
def webhook_receive():
    data = request.get_json(silent=True)

    print("POST recebido no webhook:")
    print(data)

    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
