from flask import Flask, request
import requests
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import os

app = Flask(__name__)

# =====================================================
# CONFIGURAÇÕES
# =====================================================

TOKEN = os.getenv("TOKEN_WHATSAPP")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
LINK_HUMANO = "https://wa.me"

# Menu padrão caso a variável do Railway falhe por algum motivo
MENU_PADRAO = """Olá 👋 Seja bem-vindo(a) à TEC9 Informática 🚀

Escolha uma opção:

1️⃣ Pessoa Jurídica
2️⃣ Pessoa Física
3️⃣ Falar com consultor
0️⃣ Encerrar atendimento"""

# Puxa o menu configurado direto do painel do Railway
MENU = os.getenv("MENU_TEXT", MENU_PADRAO)

# =====================================================
# CARREGAR PLANILHA
# =====================================================

print("=" * 60)
print("CARREGANDO PLANILHA TEC9")
print("=" * 60)

try:
    df = pd.read_excel("produtos.xlsx")
    df.columns = [str(col).strip().upper() for col in df.columns]

    if "DESCRIÇÃO" in df.columns:
        df.rename(columns={"DESCRIÇÃO": "DESCRICAO"}, inplace=True)
    if "PREÇO_VENDA" in df.columns:
        df.rename(columns={"PREÇO_VENDA": "PRECO"}, inplace=True)
    if "PRECO_VENDA" in df.columns:
        df.rename(columns={"PRECO_VENDA": "PRECO"}, inplace=True)

    df = df.dropna(subset=["DESCRICAO"])
    df["DESCRICAO"] = df["DESCRICAO"].astype(str)
    df["PRECO"] = pd.to_numeric(df["PRECO"], errors="coerce").fillna(0)
except Exception as e:
    print(f"Aviso: Não foi possível carregar produtos.xlsx: {e}")

# =====================================================
# MEMÓRIA DOS CLIENTES
# =====================================================

clientes = {}

# =====================================================
# ENVIAR MENSAGEM
# =====================================================

def enviar_mensagem(numero, texto):
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    requests.post(url, headers=headers, json=payload)

def resetar_cliente(numero):
    clientes[numero] = {
        "numero": numero,
        "etapa": "inicio"
    }

# =====================================================
# WEBHOOK
# =====================================================

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = "tec9"
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == verify_token:
            return challenge
        return "Erro"

    data = request.get_json()

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        mensagem = value["messages"][0]

        numero = message["from"]
        texto = message["text"]["body"].strip()
    except Exception as e:
        print(f"Evento sem mensagem: {e}")
        return "ok"

    if texto.lower() in ["menu", "reiniciar", "voltar"]:
        resetar_cliente(numero)
        enviar_mensagem(numero, MENU)
        return "ok"

    if numero not in clientes:
        resetar_cliente(numero)
        enviar_mensagem(numero, MENU)
        return "ok"

    cliente = clientes[numero]

    if cliente.get("etapa") == "com_humano":
        return "ok"

    if texto == "0":
        enviar_mensagem(numero, "✅ Atendimento encerrado.\n\nObrigado pelo contato!")
        if numero in clientes:
            del clientes[numero]
        return "ok"

    if cliente["etapa"] == "inicio":
        if texto == "1":
            cliente["tipo"] = "PJ"
            cliente["etapa"] = "aguardando_cnpj"
            enviar_mensagem(numero, "🏢 *Atendimento Pessoa Jurídica*\n\nPor favor, informe o CNPJ:\n\n0️⃣ Encerrar")
        elif texto == "2":
            cliente["tipo"] = "PF"
            cliente["etapa"] = "aguardando_nome"
            enviar_mensagem(numero, "👤 *Atendimento Pessoa Física*\n\nPor favor, informe seu Nome Completo:\n\n0️⃣ Encerrar")
        elif texto == "3":
            cliente["etapa"] = "com_humano"
            enviar_mensagem(numero, f"Perfeito 👍\n\nNossa especialista pode te ajudar agora no WhatsApp:\n\n👉 {LINK_HUMANO}")
        else:
            enviar_mensagem(numero, "Opção inválida.\n" + MENU)

    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
