from flask import Flask, request
import requests
import os
import time
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

# =========================================================
# CONFIGURAÇÕES
# =========================================================

VERIFY_TOKEN = "TEC9_TOKEN"

WHATSAPP_TOKEN = os.getenv("META_ACCESS_TOKEN")

PHONE_NUMBER_ID = "1099079283287430"

SITE_BUSCA = "https://tec9informatica.com.br/busca?q="

WHATSAPP_ESPECIALISTA = "https://wa.me/5511977315223"

ARQUIVO_EXCEL = "produtos.xlsx"

HORARIO_ATENDIMENTO = (
    "🕘 Horário de atendimento:\n"
    "Segunda a Sexta-feira\n"
    "Das 09:00 às 18:00"
)

# =========================================================
# CARREGAR PLANILHA
# =========================================================

print("\n================================================")
print("CARREGANDO PLANILHA TEC9")
print("================================================\n")

try:

    df = pd.read_excel(ARQUIVO_EXCEL)

    df.columns = [col.strip() for col in df.columns]

    print(f"TOTAL PRODUTOS: {len(df)}")

except Exception as erro:

    print("ERRO AO CARREGAR PLANILHA:")
    print(erro)

    df = pd.DataFrame()

# =========================================================
# PALAVRAS IMPORTANTES
# =========================================================

SAUDACOES = [
    "oi",
    "ola",
    "olá",
    "bom dia",
    "boa tarde",
    "boa noite",
    "menu"
]

PALAVRAS_EMPRESA = [
    "empresa",
    "cnpj",
    "corporativo",
    "servidor",
    "licitação",
    "licitacao"
]

PALAVRAS_QUENTES = [
    "comprar",
    "orcamento",
    "orçamento",
    "pedido",
    "desconto",
    "fechar",
    "pix"
]

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return "TEC9 BOT ONLINE 🚀", 200

# =========================================================
# VERIFICAÇÃO META
# =========================================================

@app.route("/webhook", methods=["GET"])
def verify_webhook():

    mode = request.args.get("hub.mode")

    token = request.args.get("hub.verify_token")

    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:

        return challenge, 200

    return "Erro de verificação", 403

# =========================================================
# RECEBER MENSAGENS
# =========================================================

@app.route("/webhook", methods=["POST"])
def receber_mensagem():

    data = request.get_json()

    print(data)

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

                texto_original = message["text"]["body"].strip()

                texto = texto_original.lower()

                print(f"MENSAGEM: {texto}")

                # =====================================================
                # MENU
                # =====================================================

                if texto in SAUDACOES:

                    enviar_menu(numero)

                # =====================================================
                # PJ
                # =====================================================

                elif texto == "1":

                    resposta = (
                        "🏢 *Atendimento Pessoa Jurídica*\n\n"
                        "Envie:\n\n"
                        "📌 CNPJ\n"
                        "📌 Nome responsável\n"
                        "📌 Produto desejado\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, resposta)

                # =====================================================
                # PF
                # =====================================================

                elif texto == "2":

                    resposta = (
                        "👤 *Atendimento Pessoa Física*\n\n"
                        "Envie:\n\n"
                        "📌 Nome\n"
                        "📌 Produto desejado\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, resposta)

                # =====================================================
                # UPGRADE
                # =====================================================

                elif texto == "3":

                    resposta = (
                        "🔧 *Upgrade / SSD / Peças*\n\n"
                        "Digite o produto desejado.\n\n"
                        "Exemplos:\n"
                        "• SSD\n"
                        "• Memória\n"
                        "• Fonte\n"
                        "• Notebook\n"
                        "• Processador\n"
                    )

                    responder_mensagem(numero, resposta)

                # =====================================================
                # GERAR ORÇAMENTO
                # =====================================================

                elif texto.startswith("orcamento") or texto.startswith("orçamento"):

                    partes = texto_original.split(";")

                    if len(partes) >= 4:

                        cliente = partes[1].strip()

                        produto = partes[2].strip()

                        quantidade = int(partes[3].strip())

                        gerar_orcamento(
                            numero,
                            cliente,
                            produto,
                            quantidade
                        )

                    else:

                        exemplo = (
                            "📄 Para gerar orçamento automático use:\n\n"
                            "orcamento; Nome Cliente; Produto; Quantidade\n\n"
                            "Exemplo:\n"
                            "orcamento; Empresa XPTO; SSD Kingston; 5"
                        )

                        responder_mensagem(numero, exemplo)

                # =====================================================
                # CNPJ
                # =====================================================

                elif detectar_cnpj(texto):

                    resposta = (
                        "🏢 Identificamos um possível atendimento corporativo.\n\n"
                        "Nossa equipe comercial dará continuidade ao atendimento.\n\n"
                        f"{WHATSAPP_ESPECIALISTA}\n\n"
                        f"{HORARIO_ATENDIMENTO}"
                    )

                    responder_mensagem(numero, resposta)

                # =====================================================
                # CLIENTE QUENTE
                # =====================================================

                elif detectar_cliente_quente(texto):

                    resposta = (
                        "🔥 Identificamos interesse comercial.\n\n"
                        "Para um atendimento mais rápido 👇\n\n"
                        f"{WHATSAPP_ESPECIALISTA}"
                    )

                    responder_mensagem(numero, resposta)

                # =====================================================
                # EMPRESA
                # =====================================================

                elif detectar_empresa(texto):

                    resposta = (
                        "🏢 Atendimento corporativo identificado.\n\n"
                        f"{WHATSAPP_ESPECIALISTA}"
                    )

                    responder_mensagem(numero, resposta)

                # =====================================================
                # BUSCA PRODUTOS
                # =====================================================

                else:

                    buscar_produtos(numero, texto_original)

    except Exception as erro:

        print("ERRO:")
        print(erro)

    return "ok", 200

# =========================================================
# MENU
# =========================================================

def enviar_menu(numero):

    mensagem = (
        "Olá 👋 Seja bem-vindo(a) à *TEC9 Informática* 🚀\n\n"
        "Escolha uma opção:\n\n"
        "1️⃣ Pessoa Jurídica\n"
        "2️⃣ Pessoa Física\n"
        "3️⃣ Upgrade / SSD / peças\n\n"
        "Ou digite diretamente o produto que procura 👇\n\n"
        "📄 Para gerar orçamento automático:\n"
        "orcamento; Nome Cliente; Produto; Quantidade\n\n"
        f"{HORARIO_ATENDIMENTO}"
    )

    responder_mensagem(numero, mensagem)

# =========================================================
# BUSCAR PRODUTOS
# =========================================================

def buscar_produtos(numero, texto_cliente):

    resultados = []

    texto_busca = texto_cliente.lower()

    for _, row in df.iterrows():

        descricao = str(row["Descrição Produto"]).lower()

        if texto_busca in descricao:

            resultados.append({
                "sku": row["SKU"],
                "descricao": row["Descrição Produto"],
                "preco": row["Preço Venda"]
            })

        if len(resultados) >= 5:
            break

    if resultados:

        mensagem = (
            f"🔎 Encontrei opções para: *{texto_cliente}*\n\n"
        )

        for item in resultados:

            mensagem += (
                f"📦 {item['descricao']}\n"
                f"💰 R$ {item['preco']}\n\n"
            )

        busca = texto_cliente.replace(" ", "+")

        mensagem += (
            f"🔗 Veja mais opções:\n"
            f"{SITE_BUSCA}{busca}\n\n"
            f"{WHATSAPP_ESPECIALISTA}"
        )

    else:

        busca = texto_cliente.replace(" ", "+")

        mensagem = (
            f"🔎 Não encontrei produtos exatos para: *{texto_cliente}*\n\n"
            f"Confira aqui:\n"
            f"{SITE_BUSCA}{busca}"
        )

    responder_mensagem(numero, mensagem)

# =========================================================
# GERAR ORÇAMENTO PDF
# =========================================================

def gerar_orcamento(numero, cliente, produto, quantidade):

    resultado = None

    produto_lower = produto.lower()

    for _, row in df.iterrows():

        descricao = str(row["Descrição Produto"]).lower()

        if produto_lower in descricao:

            resultado = row
            break

    if resultado is None:

        responder_mensagem(
            numero,
            "❌ Produto não encontrado."
        )

        return

    descricao = resultado["Descrição Produto"]

    preco = float(resultado["Preço Venda"])

    total = preco * quantidade

    nome_pdf = f"orcamento_{numero}.pdf"

    doc = SimpleDocTemplate(
        nome_pdf,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    elementos = []

    titulo = Paragraph(
        "<b>TEC9 INFORMÁTICA LTDA</b>",
        styles['Title']
    )

    elementos.append(titulo)

    elementos.append(Spacer(1, 12))

    dados_cliente = Paragraph(
        f"Cliente: {cliente}<br/>"
        f"Produto: {descricao}<br/>"
        f"Quantidade: {quantidade}",
        styles['BodyText']
    )

    elementos.append(dados_cliente)

    elementos.append(Spacer(1, 12))

    tabela = Table([
        ["Produto", "Qtd", "Valor Unitário", "Total"],
        [
            descricao,
            str(quantidade),
            f"R$ {preco:.2f}",
            f"R$ {total:.2f}"
        ]
    ])

    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))

    elementos.append(tabela)

    elementos.append(Spacer(1, 20))

    elementos.append(HRFlowable(width="100%"))

    condicoes = Paragraph(
        "<b>Condições Comerciais</b><br/>"
        "• Pagamento: À vista.<br/>"
        "• Prazo de entrega: 07 dias.<br/>"
        "• Produto sujeito à disponibilidade de estoque.<br/>"
        "• Garantia conforme fabricante.",
        styles['BodyText']
    )

    elementos.append(condicoes)

    doc.build(elementos)

    responder_mensagem(
        numero,
        "📄 Sua proposta comercial foi gerada com sucesso 😊"
    )

# =========================================================
# DETECTAR CLIENTE QUENTE
# =========================================================

def detectar_cliente_quente(texto):

    for palavra in PALAVRAS_QUENTES:

        if palavra in texto:
            return True

    return False

# =========================================================
# DETECTAR EMPRESA
# =========================================================

def detectar_empresa(texto):

    for palavra in PALAVRAS_EMPRESA:

        if palavra in texto:
            return True

    return False

# =========================================================
# DETECTAR CNPJ
# =========================================================

def detectar_cnpj(texto):

    numeros = ""

    for caractere in texto:

        if caractere.isdigit():

            numeros += caractere

    if len(numeros) >= 11:

        return True

    return False

# =========================================================
# ENVIAR WHATSAPP
# =========================================================

def responder_mensagem(numero, mensagem):

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

    try:

        resposta = requests.post(
            url,
            headers=headers,
            json=payload
        )

        print(f"STATUS: {resposta.status_code}")

        print(resposta.text)

        time.sleep(1)

    except Exception as erro:

        print(erro)

# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    porta = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=porta
    )
