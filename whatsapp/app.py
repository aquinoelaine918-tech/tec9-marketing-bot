from flask import Flask, request
import requests
import pandas as pd
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

app = Flask(__name__)

# =========================================================
# CONFIGURAÇÕES
# =========================================================

TOKEN = os.getenv("TOKEN_WHATSAPP")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

URL_WHATSAPP = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# =========================================================
# CARREGAR PLANILHA
# =========================================================

print("=" * 50)
print("CARREGANDO PLANILHA TEC9")
print("=" * 50)

df = pd.read_excel("produtos.xlsx")

print("COLUNAS ENCONTRADAS:")
print(df.columns)

# NORMALIZAÇÃO
df.columns = df.columns.str.strip()

# RENOMEAR AUTOMATICAMENTE
colunas = {}

for col in df.columns:
    nome = col.lower()

    if "sku" in nome:
        colunas[col] = "SKU"

    elif "descr" in nome:
        colunas[col] = "DESCRICAO"

    elif "pre" in nome:
        colunas[col] = "PRECO"

df.rename(columns=colunas, inplace=True)

# LIMPEZA
df["DESCRICAO"] = df["DESCRICAO"].astype(str)
df["PRECO"] = pd.to_numeric(df["PRECO"], errors="coerce")
df = df.dropna(subset=["DESCRICAO", "PRECO"])

print(df.head())

print(f"TOTAL PRODUTOS: {len(df)}")

# =========================================================
# MEMÓRIA DOS CLIENTES
# =========================================================

clientes = {}

# =========================================================
# ENVIAR MENSAGEM
# =========================================================

def enviar_mensagem(numero, mensagem):

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": mensagem
        }
    }

    requests.post(
        URL_WHATSAPP,
        headers=HEADERS,
        json=payload
    )

# =========================================================
# GERAR PDF
# =========================================================

def gerar_pdf(cliente, produto, qtd, valor_unitario, total):

    nome_arquivo = f"orcamento_{cliente}.pdf"

    doc = SimpleDocTemplate(
        nome_arquivo,
        pagesize=A4
    )

    elementos = []

    estilos = getSampleStyleSheet()

    titulo = Paragraph(
        "<b>PROPOSTA COMERCIAL TEC9 INFORMÁTICA</b>",
        estilos["Title"]
    )

    elementos.append(titulo)
    elementos.append(Spacer(1, 20))

    data = [
        ["Cliente", cliente],
        ["Produto", produto],
        ["Quantidade", str(qtd)],
        ["Valor Unitário", f"R$ {valor_unitario:,.2f}"],
        ["Valor Total", f"R$ {total:,.2f}"],
        ["Data", datetime.now().strftime("%d/%m/%Y %H:%M")]
    ]

    tabela = Table(data, colWidths=[180, 300])

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    elementos.append(tabela)
    elementos.append(Spacer(1, 20))

    rodape = Paragraph(
        """
        <b>TEC9 INFORMÁTICA</b><br/>
        Atendimento comercial especializado<br/>
        Proposta válida por 3 dias.
        """,
        estilos["Normal"]
    )

    elementos.append(rodape)

    doc.build(elementos)

    return nome_arquivo

# =========================================================
# BUSCAR PRODUTO
# =========================================================

def buscar_produto(termo):

    termo = termo.lower()

    resultado = df[
        df["DESCRICAO"].str.lower().str.contains(termo, na=False)
    ]

    return resultado.head(5)

# =========================================================
# WEBHOOK
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "BOT TEC9 ONLINE"

# =========================================================
# WEBHOOK META
# =========================================================

@app.route("/webhook", methods=["GET"])
def verificar():

    verify_token = "tec9"

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:

        if mode == "subscribe" and token == verify_token:
            return challenge, 200

    return "Erro", 403

# =========================================================
# RECEBER MENSAGENS
# =========================================================

@app.route("/webhook", methods=["POST"])
def receber():

    data = request.get_json()

    try:

        mensagem = data["entry"][0]["changes"][0]["value"]["messages"][0]

        numero = mensagem["from"]

        texto = mensagem["text"]["body"].strip()

        texto_lower = texto.lower()

        print("=" * 50)
        print("MENSAGEM RECEBIDA:")
        print(texto)
        print("=" * 50)

        # =====================================================
        # NOVO CLIENTE
        # =====================================================

        if numero not in clientes:

            clientes[numero] = {
                "etapa": "tipo_cliente"
            }

            menu = """
👋 Seja bem-vindo(a) à TEC9 Informática 🚀

Escolha uma opção:

1️⃣ Pessoa Jurídica
2️⃣ Pessoa Física

Digite apenas o número desejado.
"""

            enviar_mensagem(numero, menu)

            return "ok", 200

        etapa = clientes[numero]["etapa"]

        # =====================================================
        # ESCOLHA PF / PJ
        # =====================================================

        if etapa == "tipo_cliente":

            if texto == "1":

                clientes[numero]["tipo"] = "PJ"
                clientes[numero]["etapa"] = "cnpj"

                enviar_mensagem(
                    numero,
                    "📌 Informe o CNPJ da empresa:"
                )

            elif texto == "2":

                clientes[numero]["tipo"] = "PF"
                clientes[numero]["etapa"] = "nome"

                enviar_mensagem(
                    numero,
                    "👤 Informe seu nome:"
                )

            else:

                enviar_mensagem(
                    numero,
                    "Digite apenas:\n1️⃣ Pessoa Jurídica\n2️⃣ Pessoa Física"
                )

            return "ok", 200

        # =====================================================
        # PJ
        # =====================================================

        if etapa == "cnpj":

            clientes[numero]["cnpj"] = texto
            clientes[numero]["etapa"] = "responsavel"

            enviar_mensagem(
                numero,
                "👤 Informe o nome do responsável:"
            )

            return "ok", 200

        if etapa == "responsavel":

            clientes[numero]["responsavel"] = texto
            clientes[numero]["etapa"] = "cidade"

            enviar_mensagem(
                numero,
                "📍 Informe Cidade/UF:"
            )

            return "ok", 200

        # =====================================================
        # PF
        # =====================================================

        if etapa == "nome":

            clientes[numero]["nome"] = texto
            clientes[numero]["etapa"] = "cidade"

            enviar_mensagem(
                numero,
                "📍 Informe Cidade/UF:"
            )

            return "ok", 200

        # =====================================================
        # CIDADE
        # =====================================================

        if etapa == "cidade":

            clientes[numero]["cidade"] = texto
            clientes[numero]["etapa"] = "produto"

            enviar_mensagem(
                numero,
                """
🖥 Digite o produto desejado:

Exemplo:
- Notebook Dell
- Servidor Lenovo
- Impressora HP
- Zebra
"""
            )

            return "ok", 200

        # =====================================================
        # PRODUTO
        # =====================================================

        if etapa == "produto":

            clientes[numero]["produto"] = texto

            resultados = buscar_produto(texto)

            if resultados.empty:

                enviar_mensagem(
                    numero,
                    """
⚠️ Produto não localizado em nossa base automática.

Seu atendimento será encaminhado para nossa equipe comercial 😊
"""
                )

                clientes.pop(numero)

                return "ok", 200

            resposta = "🔎 Encontramos estas opções:\n\n"

            for i, (_, item) in enumerate(resultados.iterrows(), start=1):

                resposta += (
                    f"{i}️⃣ {item['DESCRICAO']}\n"
                    f"💰 R$ {item['PRECO']:,.2f}\n\n"
                )

            resposta += "Digite o número do produto desejado."

            clientes[numero]["resultados"] = resultados.to_dict("records")
            clientes[numero]["etapa"] = "selecionar_produto"

            enviar_mensagem(numero, resposta)

            return "ok", 200

        # =====================================================
        # SELECIONAR PRODUTO
        # =====================================================

        if etapa == "selecionar_produto":

            try:

                indice = int(texto) - 1

                produto = clientes[numero]["resultados"][indice]

                clientes[numero]["produto_escolhido"] = produto

                clientes[numero]["etapa"] = "quantidade"

                enviar_mensagem(
                    numero,
                    "📦 Informe a quantidade desejada:"
                )

            except:

                enviar_mensagem(
                    numero,
                    "Digite apenas o número do produto."
                )

            return "ok", 200

        # =====================================================
        # QUANTIDADE
        # =====================================================

        if etapa == "quantidade":

            try:

                quantidade = int(texto)

            except:

                enviar_mensagem(
                    numero,
                    "Digite apenas números."
                )

                return "ok", 200

            produto = clientes[numero]["produto_escolhido"]

            valor_unitario = float(produto["PRECO"])

            total = valor_unitario * quantidade

            clientes[numero]["quantidade"] = quantidade
            clientes[numero]["total"] = total

            resumo = f"""
📋 PRÉ-ORÇAMENTO TEC9

🖥 Produto:
{produto['DESCRICAO']}

📦 Quantidade:
{quantidade}

💰 Valor unitário:
R$ {valor_unitario:,.2f}

💵 Valor total:
R$ {total:,.2f}

Digite:

1️⃣ Receber proposta PDF
2️⃣ Falar com consultor
"""

            clientes[numero]["etapa"] = "confirmacao"

            enviar_mensagem(numero, resumo)

            return "ok", 200

        # =====================================================
        # CONFIRMAÇÃO
        # =====================================================

        if etapa == "confirmacao":

            if texto == "1":

                produto = clientes[numero]["produto_escolhido"]

                quantidade = clientes[numero]["quantidade"]

                total = clientes[numero]["total"]

                valor_unitario = produto["PRECO"]

                nome_cliente = (
                    clientes[numero].get("responsavel")
                    or clientes[numero].get("nome")
                )

                gerar_pdf(
                    nome_cliente,
                    produto["DESCRICAO"],
                    quantidade,
                    valor_unitario,
                    total
                )

                enviar_mensagem(
                    numero,
                    """
✅ Proposta comercial gerada com sucesso.

📄 PDF criado
💰 Valores calculados
🚀 Atendimento TEC9
"""
                )

                clientes.pop(numero)

                return "ok", 200

            elif texto == "2":

                enviar_mensagem(
                    numero,
                    """
👨‍💼 Seu atendimento foi direcionado para nossa equipe comercial.

Em breve um consultor TEC9 continuará o atendimento 😊
"""
                )

                clientes.pop(numero)

                return "ok", 200

            else:

                enviar_mensagem(
                    numero,
                    "Digite:\n1️⃣ PDF\n2️⃣ Consultor"
                )

                return "ok", 200

    except Exception as erro:

        print("ERRO:")
        print(erro)

    return "ok", 200

# =========================================================
# EXECUTAR
# =========================================================

if __name__ == "__main__":

    porta = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=porta
    )
