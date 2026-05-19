from flask import Flask, request
import requests
import os
import pandas as pd
import re
from datetime import datetime

# PDF
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# =========================================================
# APP
# =========================================================

app = Flask(__name__)

# =========================================================
# CONFIGURAÇÕES
# =========================================================

VERIFY_TOKEN = "TEC9_TOKEN"

WHATSAPP_TOKEN = os.getenv("META_ACCESS_TOKEN")

PHONE_NUMBER_ID = "1099079283287430"

EMPRESA = "TEC9 INFORMÁTICA"

SITE = "https://tec9informatica.com.br"

COMERCIAL = "https://wa.me/5511977315223"

HORARIO = (
    "🕒 Horário de atendimento:\n"
    "Segunda a Sexta-feira\n"
    "Das 09:00 às 18:00"
)

# =========================================================
# CARREGA PLANILHA
# =========================================================

print("===================================")
print("CARREGANDO PLANILHA TEC9")
print("===================================")

df = pd.read_excel("produtos.xlsx")

# limpa espaços dos nomes das colunas
df.columns = df.columns.str.strip()

print("COLUNAS ENCONTRADAS:")
print(df.columns)

# remove linhas vazias
df = df.dropna(subset=["Descrição"])

# remove preços zerados
df = df[df["PREÇO_VENDA"] > 0]

# garante texto
df["Descrição"] = df["Descrição"].astype(str)

print(df.head())

print(f"TOTAL PRODUTOS: {len(df)}")

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return "BOT TEC9 ONLINE", 200

# =========================================================
# VERIFICAÇÃO META
# =========================================================

@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "erro", 403

# =========================================================
# WEBHOOK
# =========================================================

@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    print("===================================")
    print("EVENTO RECEBIDO")
    print(data)
    print("===================================")

    try:

        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        messages = value.get("messages")

        if messages:

            message = messages[0]

            numero = message["from"]

            tipo = message["type"]

            if tipo == "text":

                texto = message["text"]["body"].strip()

                print(f"MENSAGEM: {texto}")

                texto_lower = texto.lower()

                # =====================================================
                # MENU INICIAL
                # =====================================================

                if (
                    texto_lower == "oi"
                    or texto_lower == "olá"
                    or texto_lower == "ola"
                    or texto_lower == "menu"
                ):

                    menu = (
                        "Olá 👋 Seja bem-vindo(a) à TEC9 Informática 🚀\n\n"

                        "Escolha uma opção:\n\n"

                        "1️⃣ Pessoa Jurídica\n"
                        "2️⃣ Pessoa Física\n"
                        "3️⃣ Upgrade / SSD / peças\n\n"

                        "Ou digite diretamente o produto que procura 👇\n\n"

                        "📄 Para gerar orçamento automático:\n"
                        "orcamento; Nome Cliente; Produto; Quantidade\n\n"

                        f"{HORARIO}"
                    )

                    responder(numero, menu)

                    return "ok", 200

                # =====================================================
                # PESSOA JURÍDICA
                # =====================================================

                elif texto == "1":

                    resposta = (
                        "🏢 Atendimento Pessoa Jurídica\n\n"

                        "Para agilizar seu atendimento envie:\n\n"

                        "📌 CNPJ\n"
                        "📌 Nome responsável\n"
                        "📌 Produto desejado\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF\n\n"

                        "Nossa equipe comercial dará continuidade 🚀\n\n"

                        f"{HORARIO}"
                    )

                    responder(numero, resposta)

                    return "ok", 200

                # =====================================================
                # PESSOA FÍSICA
                # =====================================================

                elif texto == "2":

                    resposta = (
                        "👤 Atendimento Pessoa Física\n\n"

                        "Para agilizar seu atendimento envie:\n\n"

                        "📌 Nome\n"
                        "📌 Produto desejado\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF\n\n"

                        "Nossa equipe comercial dará continuidade 🚀\n\n"

                        f"{HORARIO}"
                    )

                    responder(numero, resposta)

                    return "ok", 200

                # =====================================================
                # UPGRADE
                # =====================================================

                elif texto == "3":

                    resposta = (
                        "⚙️ Upgrade / SSD / peças\n\n"

                        "Digite o produto desejado.\n\n"

                        "Exemplos:\n"
                        "SSD Kingston\n"
                        "Memória DDR4\n"
                        "Fonte 600w\n"
                        "Processador Ryzen"
                    )

                    responder(numero, resposta)

                    return "ok", 200

                # =====================================================
                # IDENTIFICA CNPJ
                # =====================================================

                cnpj_limpo = re.sub(r"\D", "", texto)

                if len(cnpj_limpo) == 14:

                    resposta = (
                        "🏢 Atendimento corporativo identificado.\n\n"

                        "Nossa equipe comercial dará continuidade.\n\n"

                        f"{COMERCIAL}\n\n"

                        f"{HORARIO}"
                    )

                    responder(numero, resposta)

                    return "ok", 200

                # =====================================================
                # ORÇAMENTO PDF
                # =====================================================

                if texto_lower.startswith("orcamento;"):

                    try:

                        partes = texto.split(";")

                        cliente = partes[1].strip()

                        produto = partes[2].strip()

                        quantidade = int(partes[3].strip())

                        resultado = df[
                            df["Descrição"].str.contains(
                                produto,
                                case=False,
                                na=False
                            )
                        ]

                        if resultado.empty:

                            responder(
                                numero,
                                "❌ Produto não encontrado."
                            )

                            return "ok", 200

                        produto_escolhido = resultado.iloc[0]

                        sku = str(produto_escolhido["SKU"])

                        descricao = str(produto_escolhido["Descrição"])

                        preco = float(produto_escolhido["PREÇO_VENDA"])

                        total = preco * quantidade

                        gerar_pdf(
                            cliente,
                            sku,
                            descricao,
                            quantidade,
                            preco,
                            total
                        )

                        resposta = (
                            "📄 Proposta comercial gerada com sucesso.\n\n"

                            "✅ PDF criado\n"
                            "✅ Valor calculado\n"
                            "✅ Atendimento TEC9\n\n"

                            "Sua equipe já pode enviar a proposta ao cliente 🚀"
                        )

                        responder(numero, resposta)

                        return "ok", 200

                    except Exception as erro:

                        print(erro)

                        responder(
                            numero,
                            (
                                "❌ Modelo inválido.\n\n"

                                "Use:\n"

                                "orcamento; Nome Cliente; Produto; Quantidade"
                            )
                        )

                        return "ok", 200

                # =====================================================
                # BUSCA PRODUTOS
                # =====================================================

                resultado = df[
                    df["Descrição"].str.contains(
                        texto,
                        case=False,
                        na=False
                    )
                ]

                if not resultado.empty:

                    resultado = resultado.head(5)

                    mensagem = (
                        f"🔎 Encontrei opções para: {texto}\n\n"
                    )

                    for _, row in resultado.iterrows():

                        sku = str(row["SKU"])

                        descricao = str(row["Descrição"])

                        preco = float(row["PREÇO_VENDA"])

                        link = f"{SITE}/busca?q={sku}"

                        mensagem += (
                            f"📦 {descricao}\n"
                            f"💰 R$ {preco:.2f}\n"
                            f"🔗 {link}\n\n"
                        )

                    mensagem += (
                        "🤝 Atendimento comercial:\n"
                        f"{COMERCIAL}\n\n"
                        f"{HORARIO}"
                    )

                    responder(numero, mensagem)

                    return "ok", 200

                # =====================================================
                # NÃO ENCONTROU
                # =====================================================

                resposta = (
                    "❌ Não encontramos produtos relacionados.\n\n"

                    "Tente informar:\n"
                    "• Nome do produto\n"
                    "• Marca\n"
                    "• SKU\n\n"

                    f"Ou fale com nosso comercial:\n"
                    f"{COMERCIAL}"
                )

                responder(numero, resposta)

    except Exception as erro:

        print("ERRO:")
        print(erro)

    return "ok", 200

# =========================================================
# PDF
# =========================================================

def gerar_pdf(
    cliente,
    sku,
    descricao,
    quantidade,
    preco,
    total
):

    nome_arquivo = "orcamento.pdf"

    doc = SimpleDocTemplate(
        nome_arquivo,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    elementos = []

    titulo = Paragraph(
        f"<b>{EMPRESA}</b>",
        styles["Title"]
    )

    elementos.append(titulo)

    elementos.append(Spacer(1, 20))

    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    elementos.append(
        Paragraph(
            f"Cliente: {cliente}",
            styles["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            f"Data: {data}",
            styles["Normal"]
        )
    )

    elementos.append(Spacer(1, 20))

    tabela = Table([

        [
            "SKU",
            "DESCRIÇÃO",
            "QTD",
            "UNITÁRIO",
            "TOTAL"
        ],

        [
            sku,
            descricao,
            str(quantidade),
            f"R$ {preco:.2f}",
            f"R$ {total:.2f}"
        ]

    ])

    tabela.setStyle(TableStyle([

        ('BACKGROUND', (0,0), (-1,0), colors.black),

        ('TEXTCOLOR', (0,0), (-1,0), colors.white),

        ('GRID', (0,0), (-1,-1), 1, colors.black),

        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),

        ('BOTTOMPADDING', (0,0), (-1,0), 10)

    ]))

    elementos.append(tabela)

    elementos.append(Spacer(1, 30))

    elementos.append(
        Paragraph(
            "Proposta válida por 3 dias.",
            styles["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            SITE,
            styles["Normal"]
        )
    )

    doc.build(elementos)

    print("PDF GERADO COM SUCESSO")

# =========================================================
# ENVIAR MENSAGEM
# =========================================================

def responder(numero, mensagem):

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {

        "messaging_product": "whatsapp",

        "to": numero,

        "type": "text",

        "text": {
            "body": mensagem
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    print(f"STATUS: {response.status_code}")

    print(response.text)

# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080
    )
