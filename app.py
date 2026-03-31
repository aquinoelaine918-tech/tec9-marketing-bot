import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIAVEIS DE AMBIENTE
# =========================
VERIFY_TOKEN = (os.getenv("VERIFY_TOKEN") or "").strip()
ACCESS_TOKEN = (os.getenv("META_ACCESS_TOKEN") or "").strip()
PHONE_NUMBER_ID = (os.getenv("PHONE_NUMBER_ID") or "").strip()

# =========================
# TEXTOS PROFISSIONAIS
# =========================
MENSAGEM_INICIAL = (
    "Olá! Seja bem-vindo(a) à *TEC9 Informática*.\n\n"
    "Será um prazer atender você.\n"
    "Selecione uma das opções abaixo para continuar:\n\n"
    "1 - *Suporte Técnico*\n"
    "2 - *Orçamentos e Vendas*\n"
    "3 - *Atendimento com Especialista*\n\n"
    "Por favor, digite apenas o número da opção desejada."
)

MENSAGEM_SUPORTE = (
    "Você selecionou *Suporte Técnico*.\n\n"
    "Por gentileza, informe o problema apresentado no equipamento, "
    "incluindo, se possível, modelo, marca e defeito identificado.\n\n"
    "Nossa equipe técnica analisará sua solicitação o mais breve possível."
)

MENSAGEM_VENDAS = (
    "Você selecionou *Orçamentos e Vendas*.\n\n"
    "Por favor, envie o nome, modelo ou descrição do produto que deseja cotar.\n\n"
    "Se preferir, informe também:\n"
    "- quantidade desejada\n"
    "- cidade de entrega\n"
    "- se a compra será para pessoa física ou empresa\n\n"
    "Assim conseguimos agilizar seu atendimento e enviar uma proposta mais precisa."
)

MENSAGEM_ESPECIALISTA = (
    "Você selecionou *Atendimento com Especialista*.\n\n"
    "Sua solicitação foi recebida com sucesso.\n"
    "Em instantes, um especialista da *TEC9 Informática* dará continuidade ao seu atendimento."
)

MENSAGEM_PADRAO = (
    "Recebemos sua mensagem com sucesso.\n\n"
    "Para direcionarmos seu atendimento da melhor forma, digite:\n\n"
    "1 - *Suporte Técnico*\n"
    "2 - *Orçamentos e Vendas*\n"
    "3 - *Atendimento com Especialista*\n\n"
    "Se preferir, digite *OI* para visualizar novamente o menu principal."
)

MENSAGEM_NAO_TEXTO = (
    "Recebemos sua mensagem.\n\n"
    "No momento, para melhor direcionamento do atendimento, "
    "por favor envie sua solicitação em formato de texto.\n\n"
    "Digite *OI* para visualizar o menu principal."
)

# =========================
# FUNCOES AUXILIARES
# =========================
def normalizar_texto(texto):
    if not texto:
        return ""
    return texto.strip().lower()

def montar_resposta(texto_recebido):
    texto = normalizar_texto(texto_recebido)

    if texto in ["oi", "olá", "ola", "menu", "início", "inicio", "bom dia", "boa tarde", "boa noite"]:
        return MENSAGEM_INICIAL
    elif texto == "1":
        return MENSAGEM_SUPORTE
    elif texto == "2":
        return MENSAGEM_VENDAS
    elif texto == "3":
        return MENSAGEM_ESPECIALISTA
    else:
        return MENSAGEM_PADRAO

def responder_mensagem(numero, texto):
    if not ACCESS_TOKEN:
        print("META_ACCESS_TOKEN nao configurado", flush=True)
        return

    if not PHONE_NUMBER_ID:
        print("PHONE_NUMBER_ID nao configurado", flush=True)
        return

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": texto
        }
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print("STATUS ENVIO:", response.status_code, flush=True)
        print("RESPOSTA META:", response.text, flush=True)
    except Exception as e:
        print("ERRO AO ENVIAR RESPOSTA:", str(e), flush=True)

# =========================
# ROTAS
# =========================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE 🚀", 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "verify_token_configurado": bool(VERIFY_TOKEN),
        "access_token_configurado": bool(ACCESS_TOKEN),
        "phone_number_id_configurado": bool(PHONE_NUMBER_ID)
    }), 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # ---------------------------------
    # VALIDACAO DO WEBHOOK
    # ---------------------------------
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        print("VALIDACAO RECEBIDA", flush=True)
        print("hub.mode:", mode, flush=True)
        print("hub.verify_token:", token, flush=True)
        print("VERIFY_TOKEN:", VERIFY_TOKEN, flush=True)

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK VALIDADO COM SUCESSO", flush=True)
            return challenge, 200

        print("ERRO DE VERIFICACAO DO WEBHOOK", flush=True)
        return "Erro de verificacao", 403

    # ---------------------------------
    # RECEBIMENTO DE EVENTOS
    # ---------------------------------
    data = request.get_json(silent=True)
    print("WEBHOOK RECEBIDO:", data, flush=True)

    try:
        if not data:
            return jsonify({"status": "no data"}), 200

        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                # Ignora status da Meta: sent, delivered, read
                if "statuses" in value:
                    print("STATUS IGNORADO:", value.get("statuses"), flush=True)
                    continue

                # Processa apenas mensagens
                if "messages" not in value:
                    print("Evento ignorado (sem mensagem)", flush=True)
                    continue

                for message in value.get("messages", []):
                    from_number = message.get("from")
                    message_type = message.get("type", "")

                    if not from_number:
                        print("Mensagem sem remetente, ignorada.", flush=True)
                        continue

                    # Captura texto
                    if message_type == "text":
                        text_body = message.get("text", {}).get("body", "").strip()
                        print(f"MENSAGEM RECEBIDA DE {from_number}: {text_body}", flush=True)

                        resposta = montar_resposta(text_body)
                        responder_mensagem(from_number, resposta)

                    else:
                        print(f"MENSAGEM NAO TEXTO DE {from_number}: {message_type}", flush=True)
                        responder_mensagem(from_number, MENSAGEM_NAO_TEXTO)

    except Exception as e:
        print("ERRO AO PROCESSAR WEBHOOK:", str(e), flush=True)

    return jsonify({"status": "received"}), 200

# =========================
# INICIALIZACAO
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"Servidor iniciando na porta {port}", flush=True)
    app.run(host="0.0.0.0", port=port)
