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

# =====================================================
# CARREGAR PLANILHA
# =====================================================

print("=" * 60)
print("CARREGANDO PLANILHA TEC9")
print("=" * 60)

df = pd.read_excel("produtos.xlsx")

# NORMALIZA COLUNAS
df.columns = [str(col).strip().upper() for col in df.columns]

# AJUSTE NOMES
if "DESCRIÇÃO" in df.columns:
    df.rename(columns={"DESCRIÇÃO": "DESCRICAO"}, inplace=True)

if "PREÇO_VENDA" in df.columns:
    df.rename(columns={"PREÇO_VENDA": "PRECO"}, inplace=True)

if "PRECO_VENDA" in df.columns:
    df.rename(columns={"PRECO_VENDA": "PRECO"}, inplace=True)

# LIMPEZA
df = df.dropna(subset=["DESCRICAO"])

df["DESCRICAO"] = df["DESCRICAO"].astype(str)

df["PRECO"] = pd.to_numeric(
    df["PRECO"],
    errors="coerce"
).fillna(0)

print(df.columns)
print(df.head())

print(f"TOTAL PRODUTOS: {len(df)}")

# =====================================================
# MEMÓRIA DOS CLIENTES
# =====================================================

clientes = {}

# =====================================================
# MENU PRINCIPAL
# =====================================================

MENU = """
Olá 👋 Seja bem-vindo(a) à TEC9 Informática 🚀

Escolha uma opção:

1️⃣ Pessoa Jurídica
2️⃣ Pessoa Física
3️⃣ Falar com consultor
0️⃣ Encerrar atendimento
"""

# =====================================================
# ENVIAR MENSAGEM
# =====================================================

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

    requests.post(
        url,
        headers=headers,
        json=payload
    )

# =====================================================
# RESETAR CLIENTE
# =====================================================

def resetar_cliente(numero):

    clientes[numero] = {
        "numero": numero,
        "etapa": "inicio"
    }

# =====================================================
# BUSCAR PRODUTOS
# =====================================================

def buscar_produtos(texto):

    texto = texto.lower()

    resultados = df[
        df["DESCRICAO"]
        .str.lower()
        .str.contains(texto, na=False)
    ]

    return resultados.head(5)

# =====================================================
# GERAR PDF
# =====================================================

def gerar_pdf(cliente):

    nome_arquivo = f"proposta_{cliente['numero']}.pdf"

    c = canvas.Canvas(nome_arquivo, pagesize=A4)

    largura, altura = A4

    y = altura - 50

    c.setFont("Helvetica-Bold", 20)

    c.drawString(
        50,
        y,
        "PROPOSTA COMERCIAL TEC9"
    )

    y -= 50

    c.setFont("Helvetica", 12)

    c.drawString(
        50,
        y,
        f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    y -= 30

    c.drawString(
        50,
        y,
        f"Cliente: {cliente['nome']}"
    )

    y -= 25

    if cliente["tipo"] == "PJ":

        c.drawString(
            50,
            y,
            f"CNPJ: {cliente['cnpj']}"
        )

        y -= 25

    c.drawString(
        50,
        y,
        f"Cidade/UF: {cliente['cidade']}"
    )

    y -= 40

    c.setFont("Helvetica-Bold", 14)

    c.drawString(
        50,
        y,
        "PRODUTO"
    )

    y -= 30

    c.setFont("Helvetica", 12)

    c.drawString(
        50,
        y,
        cliente["produto_nome"]
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Quantidade: {cliente['quantidade']}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Valor Unitário: R$ {cliente['valor_unitario']:,.2f}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Valor Total: R$ {cliente['valor_total']:,.2f}"
    )

    y -= 50

    c.drawString(
        50,
        y,
        "Condições sujeitas à disponibilidade de estoque."
    )

    y -= 25

    c.drawString(
        50,
        y,
        "TEC9 Informática"
    )

    y -= 25

    c.drawString(
        50,
        y,
        "WhatsApp: (11) 97731-5223"
    )

    c.save()

    return nome_arquivo

# =====================================================
# ENVIAR PDF
# =====================================================

def enviar_documento(numero, arquivo):

    url_upload = (
        f"https://graph.facebook.com/v22.0/"
        f"{PHONE_NUMBER_ID}/media"
    )

    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }

    files = {
        "file": open(arquivo, "rb")
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

    url_msg = (
        f"https://graph.facebook.com/v22.0/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "document",
        "document": {
            "id": media_id,
            "filename": arquivo
        }
    }

    headers_msg = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    requests.post(
        url_msg,
        headers=headers_msg,
        json=payload
    )

# =====================================================
# WEBHOOK
# =====================================================

@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # =================================================
    # VERIFICAÇÃO META
    # =================================================

    if request.method == "GET":

        verify_token = "tec9"

        token = request.args.get("hub.verify_token")

        challenge = request.args.get("hub.challenge")

        if token == verify_token:
            return challenge

        return "Erro"

    # =================================================
    # RECEBER EVENTO
    # =================================================

    data = request.get_json()

    print("=" * 60)
    print("EVENTO RECEBIDO")
    print(data)

    try:

        mensagem = (
            data["entry"][0]["changes"][0]["value"]
            ["messages"][0]
        )

        numero = mensagem["from"]

        texto = (
            mensagem["text"]["body"]
            .strip()
        )

    except:
        return "ok"

    # =================================================
    # NOVO CLIENTE
    # =================================================

    if numero not in clientes:

        resetar_cliente(numero)

        enviar_mensagem(numero, MENU)

        return "ok"

    cliente = clientes[numero]

    # =================================================
    # SAIR
    # =================================================

    if texto == "0":

        enviar_mensagem(
            numero,
            """
✅ Atendimento encerrado.

Obrigado pelo contato com a TEC9 Informática 🚀

Quando desejar retornar basta enviar uma nova mensagem.
"""
        )

        del clientes[numero]

        return "ok"

    # =================================================
    # MENU PRINCIPAL
    # =================================================

    if cliente["etapa"] == "inicio":

        if texto == "1":

            cliente["tipo"] = "PJ"

            cliente["etapa"] = "aguardando_cnpj"

            enviar_mensagem(
                numero,
                """
🏢 Atendimento Pessoa Jurídica

Informe o CNPJ:

0️⃣ Encerrar atendimento
"""
            )

            return "ok"

        elif texto == "2":

            cliente["tipo"] = "PF"

            cliente["etapa"] = "aguardando_nome"

            enviar_mensagem(
                numero,
                """
👤 Atendimento Pessoa Física

Informe seu nome:

0️⃣ Encerrar atendimento
"""
            )

            return "ok"

        elif texto == "3":

            enviar_mensagem(
                numero,
                """
👨‍💼 Atendimento comercial TEC9:

https://wa.me/5511977315223

0️⃣ Encerrar atendimento
"""
            )

            return "ok"

        else:

            enviar_mensagem(numero, MENU)

            return "ok"

    # =================================================
    # CNPJ
    # =================================================

    if cliente["etapa"] == "aguardando_cnpj":

        cliente["cnpj"] = texto

        cliente["etapa"] = "aguardando_nome"

        enviar_mensagem(
            numero,
            """
Informe o nome do responsável:

0️⃣ Encerrar atendimento
"""
        )

        return "ok"

    # =================================================
    # NOME
    # =================================================

    if cliente["etapa"] == "aguardando_nome":

        cliente["nome"] = texto

        cliente["etapa"] = "aguardando_cidade"

        enviar_mensagem(
            numero,
            """
Informe sua cidade/UF:

Exemplo:
São Paulo/SP

0️⃣ Encerrar atendimento
"""
        )

        return "ok"

    # =================================================
    # CIDADE
    # =================================================

    if cliente["etapa"] == "aguardando_cidade":

        cliente["cidade"] = texto

        cliente["etapa"] = "aguardando_produto"

        enviar_mensagem(
            numero,
            """
Digite o produto desejado:

Exemplos:
• Servidor Dell
• Notebook Lenovo
• Impressora HP
• Headset Logitech

0️⃣ Encerrar atendimento
"""
        )

        return "ok"

    # =================================================
    # PRODUTO
    # =================================================

    if cliente["etapa"] == "aguardando_produto":

        produtos = buscar_produtos(texto)

        if produtos.empty:

            enviar_mensagem(
                numero,
                """
⚠️ Produto não encontrado.

Nosso time comercial dará continuidade no atendimento.

👨‍💼 Consultor TEC9:
https://wa.me/5511977315223

0️⃣ Encerrar atendimento
"""
            )

            resetar_cliente(numero)

            return "ok"

        cliente["produtos"] = produtos.to_dict("records")

        resposta = "🔎 Produtos encontrados:\n\n"

        for i, produto in enumerate(cliente["produtos"], start=1):

            descricao = produto["DESCRICAO"]

            preco = float(produto["PRECO"])

            resposta += (
                f"{i}️⃣ {descricao}\n"
                f"💰 R$ {preco:,.2f}\n\n"
            )

        resposta += (
            "Digite o número do produto desejado.\n\n"
            "0️⃣ Encerrar atendimento"
        )

        cliente["etapa"] = "aguardando_escolha"

        enviar_mensagem(numero, resposta)

        return "ok"

    # =================================================
    # ESCOLHA PRODUTO
    # =================================================

    if cliente["etapa"] == "aguardando_escolha":

        try:

            indice = int(texto) - 1

            produto = cliente["produtos"][indice]

        except:

            enviar_mensagem(
                numero,
                """
⚠️ Digite um número válido.

0️⃣ Encerrar atendimento
"""
            )

            return "ok"

        cliente["produto_nome"] = produto["DESCRICAO"]

        cliente["valor_unitario"] = float(produto["PRECO"])

        cliente["etapa"] = "aguardando_quantidade"

        enviar_mensagem(
            numero,
            """
Informe a quantidade desejada:

0️⃣ Encerrar atendimento
"""
        )

        return "ok"

    # =================================================
    # QUANTIDADE
    # =================================================

    if cliente["etapa"] == "aguardando_quantidade":

        try:

            quantidade = int(texto)

        except:

            enviar_mensagem(
                numero,
                """
⚠️ Informe apenas números.

0️⃣ Encerrar atendimento
"""
            )

            return "ok"

        cliente["quantidade"] = quantidade

        cliente["valor_total"] = (
            cliente["valor_unitario"] *
            quantidade
        )

        resumo = f"""
📋 PRÉ-ORÇAMENTO TEC9

👤 Cliente:
{cliente['nome']}

📍 Cidade:
{cliente['cidade']}

🖥 Produto:
{cliente['produto_nome']}

📦 Quantidade:
{cliente['quantidade']}

💰 Valor Unitário:
R$ {cliente['valor_unitario']:,.2f}

💵 Valor Total:
R$ {cliente['valor_total']:,.2f}

Escolha uma opção:

1️⃣ Receber proposta PDF
2️⃣ Falar com consultor
0️⃣ Encerrar atendimento
"""

        cliente["etapa"] = "confirmar_pdf"

        enviar_mensagem(numero, resumo)

        return "ok"

    # =================================================
    # CONFIRMAÇÃO PDF
    # =================================================

    if cliente["etapa"] == "confirmar_pdf":

        if texto == "1":

            pdf = gerar_pdf(cliente)

            enviar_documento(numero, pdf)

            enviar_mensagem(
                numero,
                """
✅ Proposta comercial enviada com sucesso.

Obrigado por escolher a TEC9 Informática 🚀

0️⃣ Encerrar atendimento
"""
            )

            resetar_cliente(numero)

            return "ok"

        elif texto == "2":

            enviar_mensagem(
                numero,
                """
👨‍💼 Consultor comercial TEC9:

https://wa.me/5511977315223

0️⃣ Encerrar atendimento
"""
            )

            resetar_cliente(numero)

            return "ok"

        else:

            enviar_mensagem(
                numero,
                """
Escolha uma opção válida:

1️⃣ Receber proposta PDF
2️⃣ Falar com consultor
0️⃣ Encerrar atendimento
"""
            )

            return "ok"

    return "ok"

# =====================================================
# INICIAR APP
# =====================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080
    )
