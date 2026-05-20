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
df["PRECO"] = pd.to_numeric(df["PRECO"], errors="coerce").fillna(0)

print(df.columns)
print(df.head())
print(f"TOTAL PRODUTOS: {len(df)}")

# =====================================================
# MEMÓRIA DOS CLIENTES
# =====================================================

clientes = {}

# =====================================================
# MENU PRINCIPAL (ITEM 3 ATUALIZADO PARA CONSULTOR)
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
    requests.post(url, headers=headers, json=payload)

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
    resultados = df[df["DESCRICAO"].str.lower().str.contains(texto, na=False)]
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
    c.drawString(50, y, "PROPOSTA COMERCIAL TEC9")
    y -= 50

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 30
    c.drawString(50, y, f"Cliente: {cliente['nome']}")
    y -= 25

    if cliente.get("tipo") == "PJ":
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

    c.drawString(50, y, "Condições sujeitas à disponibilidade de estoque.")
    y -= 25
    c.drawString(50, y, "TEC9 Informática")
    y -= 25
    c.drawString(50, y, "WhatsApp: (11) 97731-5223")
    c.save()
    return nome_arquivo

# =====================================================
# ENVIAR PDF
# =====================================================

def enviar_documento(numero, arquivo):
    url_upload = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/media"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    files = {"file": open(arquivo, "rb")}
    data = {"messaging_product": "whatsapp"}

    resposta = requests.post(url_upload, headers=headers, files=files, data=data)
    
    try:
        media_id = resposta.json()["id"]
        url_msg = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
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
        requests.post(url_msg, headers=headers_msg, json=payload)
    except Exception as e:
        print(f"Erro ao processar envio do PDF: {e}")

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
        mensagem = data["entry"][0]["changes"][0]["value"]["messages"][0]
        numero = mensagem["from"]
        texto = mensagem["text"]["body"].strip()
    except:
        return "ok"

    # =================================================
    # NOVO CLIENTE / RESET DE MENU
    # =================================================
    if texto.lower() in ["menu", "reiniciar", "voltar"]:
        resetar_cliente(numero)
        enviar_mensagem(numero, MENU)
        return "ok"

    if numero not in clientes:
        resetar_cliente(numero)
        enviar_mensagem(numero, MENU)
        return "ok"

    cliente = clientes[numero]

    # Se o cliente estiver com o humano, o bot para de interagir de forma estática
    if cliente["etapa"] == "com_humano":
        print(f"Mensagem de {numero} ignorada (em atendimento humano).")
        return "ok"

    # =================================================
    # ENCERRAR
    # =================================================
    if texto == "0":
        enviar_mensagem(
            numero,
            "✅ Atendimento encerrado.\n\nObrigado pelo contato com a TEC9 Informática 🚀\n\nQuando desejar retornar basta enviar uma nova mensagem."
        )
        del clientes[numero]
        return "ok"

    # =================================================
    # MENU PRINCIPAL - LÓGICA DE ETAPAS
    # =================================================
    if cliente["etapa"] == "inicio":
        if texto == "1":
            cliente["tipo"] = "PJ"
            cliente["etapa"] = "aguardando_cnpj"
            enviar_mensagem(numero, "🏢 *Atendimento Pessoa Jurídica*\n\nPor favor, informe o CNPJ:\n\n0️⃣ Encerrar atendimento")
        
        elif texto == "2":
            cliente["tipo"] = "PF"
            cliente["etapa"] = "aguardando_nome"
            enviar_mensagem(numero, "👤 *Atendimento Pessoa Física*\n\nPor favor, informe seu Nome Completo:\n\n0️⃣ Encerrar atendimento")
        
        elif texto == "3":
            cliente["etapa"] = "com_humano"
            mensagem_transbordo = (
                "Perfeito 👍\n\n"
                "Para um atendimento mais rápido e personalizado, nossa especialista pode te ajudar agora pelo WhatsApp:\n\n"
                f"👉 {LINK_HUMANO}"
            )
            enviar_mensagem(numero, mensagem_transbordo)
            
        else:
            enviar_mensagem(numero, "Opção inválida. Digite apenas o número correspondente.\n" + MENU)

    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
