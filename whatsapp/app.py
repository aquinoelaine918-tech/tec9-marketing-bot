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

try:
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
except Exception as e:
    print(f"Aviso: Não foi possível carregar produtos.xlsx: {e}")

# =====================================================
# MEMÓRIA DOS CLIENTES
# =====================================================

clientes = {}

# =====================================================
# MENU PRINCIPAL (ITEM 3 AJUSTADO PARA CONSULTOR)
# =====================================================

MENU = """Olá 👋 Seja bem-vindo(a) à TEC9 Informática 🚀

Escolha uma opção:

1️⃣ Pessoa Jurídica
2️⃣ Pessoa Física
3️⃣ Falar com consultor
0️⃣ Encerrar atendimento"""

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
    try:
        resultados = df[df["DESCRICAO"].str.lower().str.contains(texto, na=False)]
        return resultados.head(5)
    except:
        return []

# =====================================================
# WEBHOOK
# =====================================================

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # VERIFICAÇÃO META
    if request.method == "GET":
        verify_token = "tec9"
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == verify_token:
            return challenge
        return "Erro"

    # RECEBER EVENTO
    data = request.get_json()
    print("=" * 60)
    print("EVENTO RECEBIDO")
    print(data)

    try:
        # Estrutura com índices [0] para evitar erros de leitura da lista da Meta
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        mensagem = value["messages"][0]

        numero = mensagem["from"]
        texto = mensagem["text"]["body"].strip()
    except Exception as e:
        print(f"Ignorando notificação ou evento sem mensagem: {e}")
        return "ok"

    # COMANDOS GLOBAIS DE RETORNO
    if texto.lower() in ["menu", "reiniciar", "voltar"]:
        resetar_cliente(numero)
        enviar_mensagem(numero, MENU)
        return "ok"

    # NOVO CLIENTE
    if numero not in clientes:
        resetar_cliente(numero)
        enviar_mensagem(numero, MENU)
        return "ok"

    cliente = clientes[numero]

    # SE ESTIVER COM O HUMANO, O BOT FICA EM SILÊNCIO
    if cliente.get("etapa") == "com_humano":
        print(f"Mensagem de {numero} ignorada (atendimento com humano ativo).")
        return "ok"

    # ENCARRAR ATENDIMENTO
    if texto == "0":
        enviar_mensagem(
            numero,
            "✅ Atendimento encerrado.\n\nObrigado pelo contato com a TEC9 Informática 🚀\n\nQuando desejar retornar basta enviar uma nova mensagem."
        )
        if numero in clientes:
            del clientes[numero]
        return "ok"

    # LÓGICA DO MENU PRINCIPAL
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
