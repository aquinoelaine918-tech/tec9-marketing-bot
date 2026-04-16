import requests
import os

# ===== CONFIG =====
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Número destino (com DDI e DDD, sem espaços)
TO_NUMBER = "5511952686414"

# ===== ENVIO =====
url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "messaging_product": "whatsapp",
    "to": TO_NUMBER,
    "type": "template",
    "template": {
        "name": "teste_tec9",
        "language": {
            "code": "pt_BR"
        }
    }
}

response = requests.post(url, headers=headers, json=payload)

print("STATUS:", response.status_code)
print("RESPOSTA:", response.text)
