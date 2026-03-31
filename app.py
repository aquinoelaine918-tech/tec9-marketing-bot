import os
import requests

from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# =========================
# ENVIO TEXTO
# =========================
def enviar_texto(numero, texto):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }

    requests.post(url, json=payload, headers=headers)

# =========================
# GERAR AUDIO OPENAI
# =========================
def gerar_audio(texto):
    url = "https://api.openai.com/v1/audio/speech"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    data = {
        "model": "gpt-4o-mini-tts",
        "voice": "alloy",
        "input": texto
    }

    response = requests.post(url, headers=headers, json=data)

    with open("audio.mp3", "wb") as f:
        f.write(response.content)

    return "audio.mp3"

# =========================
# UPLOAD AUDIO META
# =========================
def upload_audio(caminho):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/media"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    files = {
        'file': ('audio.mp3', open(caminho, 'rb'), 'audio/mpeg')
    }

    data = {
        'messaging_product': 'whatsapp'
    }

    response = requests.post(url, headers=headers, files=files, data=data)

    return response.json().get("id")

# =========================
# ENVIAR AUDIO
# =========================
def enviar_audio(numero, media_id):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "audio",
        "audio": {"id": media_id}
    }

    requests.post(url, json=payload, headers=headers)

# =========================
# RESPOSTAS
# =========================
def resposta_vendas():
    return """Olá! Aqui é a Camila da TEC9 Informática.

Vou te ajudar com seu orçamento.

Para começarmos, me informe:
nome, produto, quantidade e email."""

def resposta_followup():
    return """Olá! Aqui é a Camila da TEC9.

Vi que seu atendimento ficou em andamento.

Posso continuar seu orçamento agora com você."""

# =========================
# CONTROLE VOZ (IMPORTANTE)
# =========================
def responder_com_voz(numero, texto):
    enviar_texto(numero, texto)

    try:
        audio = gerar_audio(texto)
        media_id = upload_audio(audio)
        enviar_audio(numero, media_id)
    except Exception as e:
        print("ERRO VOZ:", e)

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Erro", 403

    data = request.get_json()

    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                if "messages" in value:
                    for msg in value["messages"]:
                        numero = msg["from"]
                        texto = msg.get("text", {}).get("body", "").lower()

                        if "oi" in texto:
                            responder_com_voz(numero, resposta_vendas())

                        else:
                            enviar_texto(numero, "Digite OI para iniciar atendimento")

    except Exception as e:
        print("ERRO:", e)

    return jsonify({"ok": True})
