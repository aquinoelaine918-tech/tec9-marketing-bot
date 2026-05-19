from flask import Flask, request
import requests
import os
import threading
import time
import pandas as pd

app = Flask(__name__)

# =========================================================
# CONFIGURAÇÕES
# =========================================================

VERIFY_TOKEN = "TEC9_TOKEN"

WHATSAPP_TOKEN = os.getenv("META_ACCESS_TOKEN")

PHONE_NUMBER_ID = "1099079283287430"

SITE_BUSCA = "https://tec9informatica.com.br/busca?q="

WHATSAPP_ESPECIALISTA = "https://wa.me/5511977315223"

# =========================================================
# CARREGAR PLANILHA PRODUTOS
# =========================================================

ARQUIVO_EXCEL = "Produto sem preço de custo - Tec9Informatica (1).xlsx"

print("\n================================================")
print("CARREGANDO PLANILHA...")
print("================================================\n")

try:

    df = pd.read_excel(ARQUIVO_EXCEL)

    df = df.fillna("")

    print(f"TOTAL PRODUTOS CARREGADOS: {len(df)}")

except Exception as erro:

    print("ERRO AO CARREGAR PLANILHA:")
    print(erro)

    df = pd.DataFrame()

# =========================================================
# PALAVRAS IMPORTANTES
# =========================================================

saudacoes = [
    "oi",
    "ola",
    "olá",
    "bom dia",
    "boa tarde",
    "boa noite",
    "menu",
    "inicio",
    "início"
]

palavras_empresa = [
    "empresa",
    "cnpj",
    "corporativo",
    "servidor",
    "infraestrutura"
]

palavras_quentes = [
    "comprar",
    "orcamento",
    "orçamento",
    "desconto",
    "fechar",
    "pedido",
    "urgente",
    "pix"
]

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return "TEC9 BOT ONLINE 🚀", 200

# =========================================================
# VERIFICAÇÃO WEBHOOK
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

    print("\n================================================")
    print("EVENTO RECEBIDO:")
    print(data)
    print("================================================\n")

    try:

        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        messages = value.get("messages")

        if messages:

            message = messages[0]

            numero = message["from"]

            tipo = message["type"]

            print(f"TIPO: {tipo}")
            print(f"NUMERO: {numero}")

            if tipo == "text":

                texto_original = message["text"]["body"].strip()

                texto = texto_original.lower()

                print(f"MENSAGEM: {texto}")

                # =====================================================
                # SAUDAÇÕES
                # =====================================================

                if texto in saudacoes:

                    menu_inicial = (
                        "Olá 👋 Seja bem-vindo(a) à *TEC9 Informática* 🚀\n\n"
                        "Para agilizar seu atendimento, escolha uma opção:\n\n"
                        "1️⃣ Empresa / Pessoa Jurídica\n"
                        "2️⃣ Uso pessoal / Pessoa Física\n"
                        "3️⃣ Upgrade / SSD / peças\n\n"
                        "Ou digite diretamente o produto que procura 👇"
                    )

                    responder_mensagem(numero, menu_inicial)

                # =====================================================
                # MENU EMPRESA
                # =====================================================

                elif texto == "1":

                    resposta_pj = (
                        "🏢 *Atendimento Pessoa Jurídica*\n\n"
                        "Para agilizar seu orçamento, envie:\n\n"
                        "📌 CNPJ\n"
                        "📌 Nome do responsável\n"
                        "📌 E-mail corporativo\n"
                        "📌 Produto ou solução desejada\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF\n\n"
                        "Nossa equipe comercial dará continuidade ao atendimento 🚀"
                    )

                    responder_mensagem(numero, resposta_pj)

                # =====================================================
                # MENU PESSOA FÍSICA
                # =====================================================

                elif texto == "2":

                    resposta_pf = (
                        "👤 *Atendimento Pessoa Física*\n\n"
                        "Para prosseguirmos com seu atendimento, envie:\n\n"
                        "📌 Nome\n"
                        "📌 Produto desejado\n"
                        "📌 Quantidade\n"
                        "📌 Cidade/UF\n"
                        "📌 E-mail para proposta (opcional)\n\n"
                        "Nossa equipe comercial dará continuidade ao atendimento 🚀"
                    )

                    responder_mensagem(numero, resposta_pf)

                # =====================================================
                # MENU UPGRADE
                # =====================================================

                elif texto == "3":

                    resposta_upgrade = (
                        "🔧 *Upgrade e Peças*\n\n"
                        "Me informe qual produto você procura.\n\n"
                        "Exemplos:\n"
                        "SSD\n"
                        "Memória\n"
                        "Fonte\n"
                        "Placa de vídeo\n"
                        "Notebook\n"
                        "Processador\n"
                    )

                    responder_mensagem(numero, resposta_upgrade)

                # =====================================================
                # CLIENTE QUENTE
                # =====================================================

                elif any(palavra in texto for palavra in palavras_quentes):

                    mensagem_quente = (
                        "🔥 Identificamos interesse em atendimento comercial.\n\n"
                        "Para agilizar seu atendimento e verificar condições especiais, "
                        "fale diretamente com nossa especialista 👇\n\n"
                        f"{WHATSAPP_ESPECIALISTA}"
                    )

                    responder_mensagem(numero, mensagem_quente)

                # =====================================================
                # EMPRESA AUTOMÁTICO
                # =====================================================

                elif any(palavra in texto for palavra in palavras_empresa):

                    resposta_empresa = (
                        "🏢 Entendi que seu atendimento é corporativo.\n\n"
                        "Para um atendimento mais rápido e personalizado, "
                        "fale diretamente com nossa especialista 👇\n\n"
                        f"{WHATSAPP_ESPECIALISTA}"
                    )

                    responder_mensagem(numero, resposta_empresa)

                # =====================================================
                # BUSCA PRODUTO
                # =====================================================

                else:

                    responder_mensagem(
                        numero,
                        "🔎 Estou verificando as opções disponíveis..."
                    )

                    thread = threading.Thread(
                        target=buscar_produtos,
                        args=(numero, texto_original)
                    )

                    thread.start()

    except Exception as erro:

        print("\n================================================")
        print("ERRO AO PROCESSAR:")
        print(erro)
        print("================================================\n")

    return "ok", 200

# =========================================================
# BUSCAR PRODUTOS
# =========================================================

def buscar_produtos(numero, texto_cliente):

    try:

        time.sleep(1)

        texto_busca = texto_cliente.lower()

        resultados = []

        # =====================================================
        # PROCURA PRODUTOS
        # =====================================================

        for _, row in df.iterrows():

            nome_produto = str(row.iloc[1]).lower()

            if texto_busca in nome_produto:

                resultados.append(str(row.iloc[1]))

            if len(resultados) >= 5:
                break

        # =====================================================
        # PRODUTOS ENCONTRADOS
        # =====================================================

        if resultados:

            mensagem = (
                f"✅ Encontrei algumas opções para: *{texto_cliente}*\n\n"
            )

            for produto in resultados:

                mensagem += f"• {produto}\n"

            busca = texto_cliente.replace(" ", "+")

            link_busca = f"{SITE_BUSCA}{busca}"

            mensagem += (
                f"\n🔗 Veja mais opções:\n"
                f"{link_busca}\n\n"
                f"Se desejar atendimento especializado 👇\n"
                f"{WHATSAPP_ESPECIALISTA}"
            )

        # =====================================================
        # NENHUM PRODUTO
        # =====================================================

        else:

            busca = texto_cliente.replace(" ", "+")

            link_busca = f"{SITE_BUSCA}{busca}"

            mensagem = (
                f"🔎 Não encontrei produtos exatos para: *{texto_cliente}*\n\n"
                f"Mas você pode visualizar opções disponíveis aqui:\n\n"
                f"{link_busca}\n\n"
                f"Se desejar ajuda personalizada 👇\n"
                f"{WHATSAPP_ESPECIALISTA}"
            )

        responder_mensagem(numero, mensagem)

    except Exception as erro:

        print("\n================================================")
        print("ERRO BUSCA PRODUTOS:")
        print(erro)
        print("================================================\n")

# =========================================================
# ENVIAR MENSAGEM WHATSAPP
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

        print("\n================================================")
        print(f"STATUS ENVIO: {resposta.status_code}")
        print(f"RESPOSTA ENVIO: {resposta.text}")
        print("================================================\n")

    except Exception as erro:

        print("\n================================================")
        print("ERRO AO ENVIAR:")
        print(erro)
        print("================================================\n")

# =========================================================
# INICIAR SERVIDOR
# =========================================================

if __name__ == "__main__":

    porta = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=porta
    )
