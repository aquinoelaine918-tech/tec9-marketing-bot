import os
import re
import sqlite3
import requests
from urllib.parse import quote_plus
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIAVEIS
# =========================
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
WHATSAPP_ALERTA = os.getenv("WHATSAPP_ALERTA")

BASE_BUSCA = "https://tec9informatica.com.br/busca?q="

AGENTE = "Camila"

# =========================
# BANCO SQLITE
# =========================
conn = sqlite3.connect("leads.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telefone TEXT,
    nome TEXT,
    produto TEXT,
    quantidade TEXT,
    email TEXT,
    cnpj TEXT
)
""")
conn.commit()

# =========================
# MEMORIA
# =========================
memoria = {}

def get_memoria(numero):
    if numero not in memoria:
        memoria[numero] = {"etapa": "menu", "dados": {}}
    return memoria[numero]

# =========================
# FUNCOES
# =========================
def enviar(numero, texto):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    requests.post(url, json=payload, headers=headers)

def enviar_alerta_lead(numero_cliente, dados):
    if not WHATSAPP_ALERTA:
        return

    link = f"https://wa.me/{numero_cliente}"

    mensagem = f"""🔥 LEAD QUENTE TEC9

👤 Nome: {dados.get('nome')}
📦 Produto: {dados.get('produto')}
🔢 Quantidade: {dados.get('quantidade')}
📧 Email: {dados.get('email')}
🏢 CNPJ: {dados.get('cnpj', 'Não informado')}

👉 Abrir conversa:
{link}
"""

    enviar(WHATSAPP_ALERTA, mensagem)

def salvar_lead(numero, dados):
    cursor.execute("""
    INSERT INTO leads (telefone, nome, produto, quantidade, email, cnpj)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        numero,
        dados.get("nome"),
        dados.get("produto"),
        dados.get("quantidade"),
        dados.get("email"),
        dados.get("cnpj")
    ))
    conn.commit()

def extrair_email(texto):
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', texto)
    return match.group(0) if match else None

def extrair_cnpj(texto):
    match = re.search(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', texto)
    return match.group(0) if match else None

# =========================
# FLUXO
# =========================
def fluxo(numero, texto):
    m = get_memoria(numero)
    etapa = m["etapa"]
    dados = m["dados"]

    texto_lower = texto.lower()

    if texto_lower in ["oi", "menu"]:
        m["etapa"] = "menu"
        return """Olá! 👋 TEC9 Informática

1 - Orçamentos e Vendas
2 - Suporte Técnico
3 - Especialista"""

    if etapa == "menu":
        if texto == "1":
            m["etapa"] = "nome"
            return f"💰 {AGENTE} - Vendas\n\nQual seu nome?"
        if texto == "2":
            return "🔧 Suporte: descreva seu problema"
        if texto == "3":
            return "👤 Especialista: informe sua necessidade"

    # =========================
    # FLUXO VENDAS
    # =========================
    if etapa == "nome":
        dados["nome"] = texto
        m["etapa"] = "quantidade"
        return "Qual a quantidade?"

    if etapa == "quantidade":
        dados["quantidade"] = texto
        m["etapa"] = "produto"
        return "Qual produto ou modelo?"

    if etapa == "produto":
        dados["produto"] = texto
        m["etapa"] = "email"

        link = BASE_BUSCA + quote_plus(texto)

        return f"""Perfeito 👌

Veja opções:
👉 {link}

Agora me informe seu email"""

    if etapa == "email":
        email = extrair_email(texto)
        if not email:
            return "Informe um email válido"

        dados["email"] = email
        m["etapa"] = "cnpj"

        return "Se for empresa, envie CNPJ ou digite NAO"

    if etapa == "cnpj":
        cnpj = extrair_cnpj(texto)

        if cnpj:
            dados["cnpj"] = cnpj
        else:
            dados["cnpj"] = "Não informado"

        # SALVA LEAD
        salvar_lead(numero, dados)

        # ALERTA
        enviar_alerta_lead(numero, dados)

        m["etapa"] = "final"

        return """✅ Recebido!

Seu orçamento está sendo preparado.

Um especialista vai te atender agora."""

    return "Digite OI para começar"

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
                        texto = msg.get("text", {}).get("body", "")

                        resposta = fluxo(numero, texto)
                        enviar(numero, resposta)

    except Exception as e:
        print("ERRO:", e)

    return jsonify({"ok": True})
