from flask import Flask, request
import requests

app = Flask(__name__)

# 🔐 TOKEN DE VERIFICAÇÃO (igual da Meta)
VERIFY_TOKEN = "tec9token123"

# 🔑 COLE SEU TOKEN DA META AQUI
ACCESS_TOKEN = "EAAM78ivqOXwBRIGa0Gg8jajAv4jI2VKbVDYAWTECi02KAUrTD1cL2vE6X0DywI3d9G77tLHgpz7694Xp5OTHuSYZBIIQzglKsd8NFLVmBQa3MbFWVpwnoH3BkE8biAjb9VNhQVmxAjjKcIQELW0VSEZArVqECbi6nFc1de05ZCOYH2RqFWYUJfKzBZBTsSGD34xOigJ97EtVwtK4aO9H2AxhwMYCdIaLbR7kUJBK6cOP0AfFBhrpm7dkGRiPlBkzXbJObBJyhEFZB7h0Dnx5Ri86p"


# ===============================
# 🔹 VERIFICAÇÃO DO WEBHOOK
# ===============================
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge
    return "Erro", 403


# ===============================
# 🔹 RECEBER MENSAGENS
# ===============================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Recebido:", data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]

            from_number = message["from"]
            phone_number_id = value["metadata"]["phone_number_id"]

            texto = message["text"]["body"]

            print("Mensagem:", texto)

            # 🤖 RESPOSTA AUTOMÁTICA
            resposta = f"Olá! 👋 Recebi sua mensagem: {texto}\n\nSou a TEC9 Informática e vou te ajudar agora."

            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"

            headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": "text",
                "text": {"body": resposta}
            }

            requests.post(url, headers=headers, json=payload)

    except Exception as e:
        print("Erro:", e)

    return "ok", 200


# ===============================
# 🔹 RODAR SERVIDOR
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
