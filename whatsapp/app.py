import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "OK", 200

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

@app.route("/webhook", methods=["GET"])
def verify():
    return "WEBHOOK OK", 200

@app.route("/webhook", methods=["POST"])
def receive():
    return "ok", 200

# ESSENCIAL PARA RAILWAY
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
