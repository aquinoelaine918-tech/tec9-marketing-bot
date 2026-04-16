import requests

# =========================================
# CONFIGURAÇÕES (AJUSTE AQUI)
# =========================================

ACCESS_TOKEN = "SEU_TOKEN_AQUI"  # <-- COLE O TOKEN NOVO AQUI
PHONE_NUMBER_ID = "1099079283287430"  # já está correto
TO_NUMBER = "5511952686414"  # número que vai receber

# =========================================
# ENVIO DA MENSAGEM
# =========================================

url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

data = {
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

# =========================================
# REQUISIÇÃO
# =========================================

response = requests.post(url, headers=headers, json=data)

# =========================================
# RESULTADO
# =========================================

print("Status Code:", response.status_code)
print("Resposta da API:")
print(response.json())
