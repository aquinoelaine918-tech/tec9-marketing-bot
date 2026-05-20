from flask import Flask, request
import requests
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import os

app = Flask(__name__)

# ==========================================
# CONFIGURAÇÕES
# ==========================================

TOKEN = os.getenv("TOKEN_WHATSAPP")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# ==========================================
# CARREGAR PLANILHA
# ==========================================

print("=" * 40)
print("CARREGANDO PLANILHA TEC9")
print("=" * 40)

df = pd.read_excel("produtos.xlsx")

print("COLUNAS ENCONTRADAS:")
print(df.columns)

# NORMALIZA COLUNAS
df.columns = [str(col).strip().upper() for col in df.columns]

# RENOMEIA
if "DESCRIÇÃO" in df.columns:
    df.rename(columns={"DESCRIÇÃO": "DESCRICAO"}, inplace=True)

if "PREÇO_VENDA" in df.columns:
    df.rename(columns={"PREÇO_VENDA": "PRECO"}, inplace=True)

if "PRECO_VENDA" in df.columns:
    df.rename(columns={"PRECO_VENDA": "PRECO"}, inplace=True)

print(df.head())

print(f"TOTAL PRODUTOS: {len(df)}")

# ==========================================
# MEMÓRIA DOS CLIENTES
# ==========================================

clientes = {}

# ==========================================
# ENVIAR MENSAGEM
# ==========================================

def enviar_mensagem(numero, texto):

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": texto
        }
    }

    requests.post(url, headers=headers, json=payload)

# ==========================================
# BUSCAR PRODUTOS
# ==========================================

def buscar_produtos(texto):

    texto = texto.lower()

    resultados = df[
        df["DESCRICAO"]
        .astype(str)
        .str.lower()
        .str.contains(texto, na=False)
    ]

    return resultados.head(5)

# ==========================================
# GERAR PDF
# ==========================================

def gerar_pdf(cliente):

    nome_arquivo = f"proposta_{cliente['numero']}.pdf"

    c = canvas.Canvas(nome_arquivo, pagesize=A4)

    largura, altura = A4

    y = altura - 50

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "PROPOSTA COMERCIAL - TEC9")

    y -= 40

    c.setFont("Helvetica", 12)

    c.drawString(50, y, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    y -= 30

    c.drawString(50, y, f"Cliente: {cliente['nome']}")

    y -= 25

    if cliente["tipo"] == "PJ":
        c.drawString(50, y, f"CNPJ: {cliente['cnpj']}")
        y -= 25

    c.drawString(50, y, f"Cidade/UF: {cliente['cidade']}")

    y -= 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "PRODUTO")

    y -= 30

    c.setFont("Helvetica", 12)

    c.drawString(50, y, cliente["produto_nome"])

    y -= 25

    c.drawString(50, y, f"Quantidade: {cliente['quantidade']}")

    y -= 25

    c.drawString(50, y, f"Valor Unitário: R$ {cliente['valor_unitario']:,.2f}")

    y -= 25

    c.drawString(50, y, f"Valor Total: R$ {cliente['valor_total']:,.2f}")

    y -= 50

    c.drawString(50, y, "Condições comerciais sujeitas à disponibilidade.")

    y -= 25

    c.drawString(50, y, "Atendimento TEC9 Informática")

    y -= 25

    c.drawString(50, y, "WhatsApp: (11) 97731-5223")

    c.save()

    return nome_arquivo

# ==========================================
# ENVIAR DOCUMENTO
# ==========================================

def enviar_documento(numero, caminho_arquivo):

    url_upload = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/media"

    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }

    files = {
        "file": open(caminho_arquivo, "rb")
    }

    data = {
        "messaging_product": "whatsapp"
    }

    resposta = requests.post(
        url_upload,
        headers=headers,
        files=files,
        data=data
    )

    media_id = resposta.json()["id"]

    url_msg = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "document",
        "document": {
            "id": media_id,
            "filename": caminho_arquivo
        }
    }

    headers_msg = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    requests.post(url_msg, headers=headers_msg, json=payload)

# ==========================================
# MENU INICIAL
# ==========================================

def menu_inicial():

    return """
Olá 👋 Seja bem-vindo(a) à TEC9 Informática 🚀

Escolha uma opção:

1️⃣ Pessoa Jurídica
2️⃣ Pessoa Física
3️⃣ Falar com consultor
0️⃣ Encerrar atendimento
"""

# ==========================================
# WEBHOOK
# ==========================================

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

    print("=" * 50)
    print("EVENTO RECEBIDO")
    print(data)

    try:

        mensagem = data["entry"][0]["changes"][0]["value"]["messages"][0]

        numero = mensagem["from"]

        texto = mensagem["text"]["body"].strip()

        texto_lower = texto.lower()

    except:
        return "ok"

    # ======================================
    # NOVO CLIENTE
    # ======================================

    if numero not in clientes:

        clientes[numero] = {
            "etapa": "inicio",
            "numero": numero
        }

        enviar_mensagem(numero, menu_inicial())

        return "ok"

    cliente = clientes[numero]

    # ======================================
    # ENCERRAR
    # ======================================

    if texto == "0":

        enviar_mensagem(
            numero,
            """
✅ Atendimento encerrado.

A TEC9 Informática agradece seu contato 🚀
"""
        )

        del clientes[numero]

        return "ok"

    # ======================================
    # MENU
    # ======================================

    if cliente["etapa"] == "inicio":

        if texto == "1":

            cliente["tipo"] = "PJ"
            cliente["etapa"] = "aguardando_cnpj"

            enviar_mensagem(numero, "Informe o CNPJ:")

            return "ok"

        elif texto == "2":

            cliente["tipo"] = "PF"
            cliente["etapa"] = "aguardando_nome"

            enviar_mensagem(numero, "Informe seu nome:")

            return "ok"

        elif texto == "3":

            enviar_mensagem(
                numero,
                """
👨‍💼 Consultor TEC9:
https://wa.me/5511977315223
"""
            )

            return "ok"

        else:

            enviar_mensagem(numero, menu_inicial())

            return "ok"

    # ======================================
    # CNPJ
    # ======================================

    if cliente["etapa"] == "aguardando_cnpj":

        cliente["cnpj"] = texto
        cliente["etapa"] = "aguardando_nome"

        enviar_mensagem(numero, "Informe o nome do responsável:")

        return "ok"

    # ======================================
    # NOME
    # ======================================

    if cliente["etapa"] == "aguardando_nome":

        cliente["nome"] = texto
        cliente["etapa"] = "aguardando_cidade"

        enviar_mensagem(numero, "Informe sua cidade/UF:")

        return "ok"

    # ======================================
    # CIDADE
    # ======================================

    if cliente["etapa"] == "aguardando_cidade":

        cliente["cidade"] = texto
        cliente["etapa"] = "aguardando_produto"

        enviar_mensagem(
            numero,
            """
Digite o produto desejado:

Exemplo:
Servidor Lenovo
Notebook Dell
Impressora HP
"""
        )

        return "ok"

    # ======================================
    # BUSCAR PRODUTO
    # ======================================

    if cliente["etapa"] == "aguardando_produto":

        produtos = buscar_produtos(texto)

        if produtos.empty:

            enviar_mensagem(
                numero,
                """
⚠️ Não localizamos o produto informado.

Nossa equipe comercial continuará o atendimento.

👨‍💼 Consultor TEC9:
https://wa.me/5511977315223
"""
            )

            cliente["etapa"] = "inicio"

            return "ok"

        cliente["produtos_encontrados"] = produtos.to_dict("records")

        resposta = "🔎 Encontramos estas opções:\n\n"

        for i, produto in enumerate(cliente["produtos_encontrados"], start=1):

            descricao = str(produto["DESCRICAO"])

            preco = float(produto["PRECO"])

            resposta += (
                f"{i}️⃣ {descricao}\n"
                f"💰 R$ {preco:,.2f}\n\n"
            )

        resposta += "Digite o número desejado."

        cliente["etapa"] = "aguardando_escolha"

        enviar_mensagem(numero, resposta)

        return "ok"

    # ======================================
    # ESCOLHA PRODUTO
    # ======================================

    if cliente["etapa"] == "aguardando_escolha":

        try:

            indice = int(texto) - 1

            produto = cliente["produtos_encontrados"][indice]

        except:

            enviar_mensagem(numero, "Digite um número válido.")

            return "ok"

        cliente["produto_nome"] = produto["DESCRICAO"]
        cliente["valor_unitario"] = float(produto["PRECO"])

        cliente["etapa"] = "aguardando_quantidade"

        enviar_mensagem(numero, "Informe a quantidade desejada:")

        return "ok"

    # ======================================
    # QUANTIDADE
    # ======================================

    if cliente["etapa"] == "aguardando_quantidade":

        try:

            quantidade = int(texto)

        except:

            enviar_mensagem(numero, "Digite apenas números.")

            return "ok"

        cliente["quantidade"] = quantidade

        cliente["valor_total"] = (
            cliente["valor_unitario"] * quantidade
        )

        resposta = f"""
📋 Pré-Orçamento TEC9

👤 Cliente: {cliente['nome']}
📍 Cidade: {cliente['cidade']}

🖥 Produto:
{cliente['produto_nome']}

📦 Quantidade: {cliente['quantidade']}

💰 Valor unitário:
R$ {cliente['valor_unitario']:,.2f}

💵 Valor total:
R$ {cliente['valor_total']:,.2f}

Escolha:

1️⃣ Receber proposta PDF
2️⃣ Falar com consultor
0️⃣ Encerrar atendimento
"""

        cliente["etapa"] = "confirmar_pdf"

        enviar_mensagem(numero, resposta)

        return "ok"

    # ======================================
    # CONFIRMAR PDF
    # ======================================

    if cliente["etapa"] == "confirmar_pdf":

        if texto == "1":

            pdf = gerar_pdf(cliente)

            enviar_documento(numero, pdf)

            enviar_mensagem(
                numero,
                """
✅ Proposta comercial enviada com sucesso.

TEC9 Informática 🚀
"""
            )

            cliente["etapa"] = "inicio"

            return "ok"

        elif texto == "2":

            enviar_mensagem(
                numero,
                """
👨‍💼 Consultor TEC9:
https://wa.me/5511977315223
"""
            )

            cliente["etapa"] = "inicio"

            return "ok"

        else:

            enviar_mensagem(
                numero,
                "Digite 1 para PDF ou 2 para consultor."
            )

            return "ok"

    return "ok"

# ==========================================
# START
# ==========================================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=8080)
