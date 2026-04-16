import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "TEC9 BOT ONLINE"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
