from flask import Flask, request
import requests
import os
import urllib.parse

app = Flask(__name__)

VERIFY_TOKEN = "TEC9_TOKEN"
WHATSAPP_TOKEN = os.getenv("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = "1099079283287430"
LINK_HUMANO = "https://wa.me/5511977315223"

# Dicionário na memória para controlar as etapas do funil de cada cliente
estados_clientes = {}

@app.route("/")
def home():
    return "TEC9 BOT COMMERCIAL ONLINE 🚀", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Erro de verificação", 403

def verificar_gatilhos_humano(texto):
    """Retorna True se o cliente usar qualquer palavra que exija transbordo imediato"""
    gatilhos = [
        "desconto", "proposta", "cnpj", "servidor", "urgente", "urgencia", 
        "prazo", "comprar", "fechar", "falar com atendente", "humano", 
        "especialista", "vendedor", "quantidade", "volume", "licitação"
    ]
    return any(gatilho in texto for gatilho in gatilhos)

@app.route("/webhook", methods=["POST"])
def receber_mensagem():
    data = request.get_json()
    
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
                texto_cliente = message["text"]["body"].strip()
                texto_minusculo = texto_cliente.lower()
                
                # Resgata ou define o estado inicial do cliente
                estado_atual = estados_clientes.get(numero, "inicio")

                # Comandos globais de reinicialização
                if texto_minusculo in ["menu", "reiniciar", "voltar"]:
                    estado_atual = "inicio"

                # Se o cliente já foi encaminhado para o humano, o bot silencia (Regra de Transbordo)
                if estado_atual == "com_humano" and texto_minusculo != "menu":
                    print(f"Bot omitido. Cliente {numero} em atendimento humano.")
                    return "ok", 200

                # Verificação instantânea de gatilhos comerciais para transbordo
                if verificar_gatilhos_humano(texto_minusculo):
                    mensagem_transbordo = (
                        "Perfeito 👍\n\n"
                        "Para um atendimento mais rápido e personalizado, nossa especialista pode te ajudar agora pelo WhatsApp:\n\n"
                        "👉 " + LINK_HUMANO
                    )
                    responder_mensagem(numero, mensagem_transbordo)
                    estados_clientes[numero] = "com_humano"
                    return "ok", 200

                # ========================================================
                # ETAPA 1 — MENSAGEM INICIAL / MENU PRINCIPAL
                # ========================================================
                if estado_atual == "inicio":
                    menu_inicial = (
                        "Olá, seja bem-vindo à Tec9 Informática 😊\n\n"
                        "Para agilizar seu atendimento, escolha uma opção:\n\n"
                        "1 - Produtos para uso pessoal\n"
                        "2 - Soluções para empresa\n"
                        "3 - Upgrade / peças / SSD"
                    )
                    responder_mensagem(numero, menu_inicial)
                    estados_clientes[numero] = "aguardando_menu_principal"

                # ========================================================
                # ETAPA 2 — CONDITION BRANCH PRINCIPAL
                # ========================================================
                elif estado_atual == "aguardando_menu_principal":
                    if texto_cliente == "1":
                        # BRANCH 1 — Uso Pessoal
                        menu_pf = (
                            "Perfeito 😊\n\n"
                            "Você procura qual tipo de produto?\n\n"
                            "1 - Notebook\n"
                            "2 - Computador\n"
                            "3 - Gamer\n"
                            "4 - Acessórios\n"
                            "5 - Outro produto"
                        )
                        responder_mensagem(numero, menu_pf)
                        estados_clientes[numero] = "aguardando_categoria_pf"

                    elif texto_cliente == "2":
                        # BRANCH 2 — Empresa / PJ
                        menu_pj = (
                            "Perfeito 👍\n\n"
                            "Seu atendimento é para empresa.\n\n"
                            "Para agilizar, me informe qual solução você procura:\n\n"
                            "1 - Notebook corporativo\n"
                            "2 - Servidor\n"
                            "3 - Upgrade de máquinas\n"
                            "4 - Infraestrutura / TI\n"
                            "5 - Outro"
                        )
                        responder_mensagem(numero, menu_pj)
                        estados_clientes[numero] = "aguardando_categoria_pj"

                    elif texto_cliente == "3":
                        # BRANCH 3 — Upgrade / Peças / SSD
                        menu_upgrade = (
                            "Perfeito 👍\n\n"
                            "Para ajudar melhor, me informe qual peça você procura.\n\n"
                            "Exemplos:\n"
                            "SSD\n"
                            "Memória\n"
                            "HD\n"
                            "Fonte\n"
                            "Placa de vídeo\n"
                            "Processador\n"
                            "Gabinete"
                        )
                        responder_mensagem(numero, menu_upgrade)
                        estados_clientes[numero] = "ia_busca_produtos"

                    else:
                        # BRANCH NONE — Resposta Inválida
                        menu_invalido = (
                            "Não consegui identificar sua opção.\n\n"
                            "Por favor responda com um número:\n\n"
                            "1 - Produtos para uso pessoal\n"
                            "2 - Soluções para empresa\n"
                            "3 - Upgrade, SSD, peças e acessórios\n\n"
                            "Se preferir atendimento direto, fale com nossa especialista no WhatsApp:\n\n"
                            "👉 " + LINK_HUMANO
                        )
                        responder_mensagem(numero, menu_invalido)

                # ========================================================
                # ETAPA 3 — SUB-CATEGORIAS (QUALIFICAÇÃO FINAL)
                # ========================================================
                elif estado_atual in ["aguardando_categoria_pf", "aguardando_categoria_pj"]:
                    # Valida se o cliente escolheu uma opção válida ou digitou texto direto
                    opcoes_validas = ["1", "2", "3", "4", "5"]
                    
                    if texto_cliente in opcoes_validas:
                        msg_Transicao_ia = (
                            "Entendido! Estou checando as melhores opções no sistema.\n\n"
                            "O que exatamente você busca nessa categoria? Pode digitar o modelo ou componente (Ex: i5, 16GB, Ryzen, Dell) 👇"
                        )
                        responder_mensagem(numero, msg_Transicao_ia)
                        estados_clientes[numero] = "ia_busca_produtos"
                    else:
                        # Se digitar texto direto, já joga para o interpretador de produtos
                        estado_atual = "ia_busca_produtos"

                # ========================================================
                # ETAPA 4 — SISTEMA INTELIGENTE DE BUSCA (PRÉ-IA CONTROLADA)
                # ========================================================
                if estado_atual == "ia_busca_produtos" or estados_clientes.get(numero) == "ia_busca_produtos":
                    # Transforma a entrada do cliente em um termo de busca seguro para URL
                    termo_url = urllib.parse.quote(texto_cliente.strip())
                    url_busca = f"https://tec9informatica.com.br/busca?q={termo_url}"

                    resposta_busca = (
                        f"Perfeito 👍\n\n"
                        f"Temos diversas opções disponíveis relacionadas a '{texto_cliente}'.\n\n"
                        f"Veja os modelos e preços atualizados direto no nosso site:\n"
                        f"👉 {url_busca}\n\n"
                        f"Se encontrar o modelo ideal ou quiser fechar o pedido, basta avisar por aqui para eu te conectar com um vendedor! 🚀"
                    )
                    responder_mensagem(numero, resposta_busca)
                    # Mantém o estado aqui para permitir múltiplas buscas até o transbordo humano
                    estados_clientes[numero] = "ia_busca_produtos"

    except Exception as erro:
        print("ERRO AO PROCESSAR:", erro)

    return "ok", 200

def responder_mensagem(numero, mensagem):
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": message}
    }
    try:
        resposta = requests.post(url, headers=headers, json=payload)
        print(f"STATUS ENVIO: {resposta.status_code}")
    except Exception as e:
        print(f"Falha ao enviar: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
