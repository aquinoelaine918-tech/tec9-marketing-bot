import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIAVEIS DE AMBIENTE
# =========================
VERIFY_TOKEN = (os.getenv("VERIFY_TOKEN") or "").strip()
ACCESS_TOKEN = (os.getenv("META_ACCESS_TOKEN") or "").strip()
PHONE_NUMBER_ID = (os.getenv("PHONE_NUMBER_ID") or "").strip()

# =========================
# AGENTES TEC9
# =========================
AGENTE_VENDAS = "Camila"
AGENTE_SUPORTE = "Lucas"
AGENTE_ESPECIALISTA = "Ricardo"

# =========================
# MEMORIA EM RAM
# =========================
memoria_clientes = {}

# Estrutura exemplo:
# memoria_clientes["5511999999999"] = {
#     "setor": "vendas",
#     "etapa": "aguardando_nome",
#     "dados": {
#         "nome": "",
#         "produto": "",
#         "quantidade": "",
#         "email": "",
#         "cnpj": "",
#         "marca": "",
#         "modelo": "",
#         "duvida": "",
#         "defeito": ""
#     }
# }

# =========================
# PALAVRAS-CHAVE
# =========================
PALAVRAS_MENU = [
    "oi", "olá", "ola", "menu", "inicio", "início", "bom dia", "boa tarde", "boa noite"
]

PALAVRAS_REINICIAR = [
    "menu", "inicio", "início", "reiniciar", "recomeçar", "voltar", "sair"
]

PALAVRAS_CLIENTE_QUENTE = [
    "preco", "preço", "valor", "quanto custa", "orcamento", "orçamento",
    "prazo", "entrega", "estoque", "disponivel", "disponível",
    "pagamento", "pix", "boleto", "cartao", "cartão", "comprar",
    "cotacao", "cotação", "pedido", "frete", "urgente"
]

# =========================
# FUNCOES AUXILIARES
# =========================
def normalizar_texto(texto):
    return texto.strip().lower() if texto else ""

def extrair_email(texto):
    if not texto:
        return None
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', texto)
    return match.group(0) if match else None

def extrair_cnpj(texto):
    if not texto:
        return None
    match = re.search(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', texto)
    return match.group(0) if match else None

def contem_palavra(texto, palavras):
    texto_norm = normalizar_texto(texto)
    return any(p in texto_norm for p in palavras)

def cliente_quente(texto):
    return contem_palavra(texto, PALAVRAS_CLIENTE_QUENTE)

def iniciar_memoria(numero):
    memoria_clientes[numero] = {
        "setor": None,
        "etapa": "menu_principal",
        "dados": {
            "nome": "",
            "produto": "",
            "quantidade": "",
            "email": "",
            "cnpj": "",
            "marca": "",
            "modelo": "",
            "duvida": "",
            "defeito": ""
        }
    }

def obter_memoria(numero):
    if numero not in memoria_clientes:
        iniciar_memoria(numero)
    return memoria_clientes[numero]

def limpar_memoria(numero):
    iniciar_memoria(numero)

def menu_principal():
    return (
        "Olá! Seja bem-vindo(a) à *TEC9 Informática*.\n\n"
        "Você será atendido(a) por nossa equipe especializada:\n\n"
        f"1 - *{AGENTE_VENDAS}* | Orçamentos e Vendas\n"
        f"2 - *{AGENTE_SUPORTE}* | Suporte Técnico\n"
        f"3 - *{AGENTE_ESPECIALISTA}* | Especialista TEC9\n\n"
        "Digite apenas o número da opção desejada."
    )

def resposta_cliente_quente():
    return (
        f"🔥 *{AGENTE_VENDAS} | Atendimento Comercial Prioritário*\n\n"
        "Perfeito. Vou te ajudar com prioridade.\n\n"
        "Para começarmos, por favor informe seu *nome*."
    )

def resposta_nao_texto():
    return (
        "Recebemos sua mensagem.\n\n"
        "No momento, para dar continuidade ao atendimento, pedimos por gentileza que envie sua solicitação em formato de texto.\n\n"
        "Digite *OI* para visualizar o menu principal."
    )

# =========================
# FLUXO VENDAS
# =========================
def iniciar_fluxo_vendas(memoria):
    memoria["setor"] = "vendas"
    memoria["etapa"] = "aguardando_nome"
    return (
        f"💰 *{AGENTE_VENDAS} | Orçamentos e Vendas*\n\n"
        "Vou te ajudar com seu orçamento.\n\n"
        "Para começarmos, por favor informe seu *nome*."
    )

def processar_fluxo_vendas(texto, memoria):
    dados = memoria["dados"]
    etapa = memoria["etapa"]

    if etapa == "aguardando_nome":
        dados["nome"] = texto.strip()
        memoria["etapa"] = "aguardando_quantidade"
        return (
            f"Prazer, *{dados['nome']}*.\n\n"
            "Agora, por favor informe a *quantidade desejada*."
        )

    if etapa == "aguardando_quantidade":
        dados["quantidade"] = texto.strip()
        memoria["etapa"] = "aguardando_produto"
        return (
            "Perfeito.\n\n"
            "Agora me informe o *nome do produto ou modelo* que você procura."
        )

    if etapa == "aguardando_produto":
        dados["produto"] = texto.strip()
        memoria["etapa"] = "aguardando_email"
        return (
            "Ótimo.\n\n"
            "Agora, por favor informe seu *email* para envio da proposta."
        )

    if etapa == "aguardando_email":
        email = extrair_email(texto)
        if not email:
            return (
                "Por favor, envie um *email válido* para continuarmos.\n\n"
                "Exemplo: nome@empresa.com.br"
            )

        dados["email"] = email
        memoria["etapa"] = "aguardando_cnpj_ou_finalizacao"
        return (
            "Perfeito. Recebemos seu email.\n\n"
            "Se a compra for para *empresa*, informe agora o *CNPJ*.\n\n"
            "Se não for compra empresarial, responda apenas com:\n"
            "*NAO TENHO CNPJ*"
        )

    if etapa == "aguardando_cnpj_ou_finalizacao":
        texto_norm = normalizar_texto(texto)
        cnpj = extrair_cnpj(texto)

        if cnpj:
            dados["cnpj"] = cnpj
            memoria["etapa"] = "finalizado_vendas"
            return (
                f"✅ *{AGENTE_VENDAS} | Consultora Comercial TEC9*\n\n"
                "Perfeito. Recebemos suas informações para atendimento corporativo.\n\n"
                "Resumo do atendimento:\n"
                f"- Nome: {dados['nome']}\n"
                f"- Quantidade: {dados['quantidade']}\n"
                f"- Produto/Modelo: {dados['produto']}\n"
                f"- Email: {dados['email']}\n"
                f"- CNPJ: {dados['cnpj']}\n\n"
                "Sua solicitação foi encaminhada para análise comercial.\n"
                "Em breve daremos continuidade com a proposta."
            )

        if texto_norm in ["nao tenho cnpj", "não tenho cnpj", "nao", "não", "pf", "pessoa fisica", "pessoa física"]:
            memoria["etapa"] = "finalizado_vendas"
            return (
                f"✅ *{AGENTE_VENDAS} | Consultora Comercial TEC9*\n\n"
                "Perfeito. Recebemos suas informações.\n\n"
                "Resumo do atendimento:\n"
                f"- Nome: {dados['nome']}\n"
                f"- Quantidade: {dados['quantidade']}\n"
                f"- Produto/Modelo: {dados['produto']}\n"
                f"- Email: {dados['email']}\n\n"
                "Sua solicitação foi encaminhada para análise comercial.\n"
                "Em breve daremos continuidade com a proposta."
            )

        return (
            "Se a compra for para empresa, envie o *CNPJ*.\n\n"
            "Se não for compra empresarial, responda apenas:\n"
            "*NAO TENHO CNPJ*"
        )

    if etapa == "finalizado_vendas":
        return (
            f"💰 *{AGENTE_VENDAS} | Consultora Comercial TEC9*\n\n"
            "Seu atendimento comercial já foi registrado.\n\n"
            "Se desejar iniciar um novo atendimento, digite *MENU*."
        )

    memoria["etapa"] = "aguardando_nome"
    return (
        f"💰 *{AGENTE_VENDAS} | Orçamentos e Vendas*\n\n"
        "Vamos começar novamente.\n\n"
        "Por favor, informe seu *nome*."
    )

# =========================
# FLUXO SUPORTE
# =========================
def iniciar_fluxo_suporte(memoria):
    memoria["setor"] = "suporte"
    memoria["etapa"] = "aguardando_marca"
    return (
        f"🔧 *{AGENTE_SUPORTE} | Suporte Técnico TEC9*\n\n"
        "Vou dar sequência ao seu atendimento.\n\n"
        "Para começarmos, informe a *marca do equipamento*."
    )

def processar_fluxo_suporte(texto, memoria):
    dados = memoria["dados"]
    etapa = memoria["etapa"]

    if etapa == "aguardando_marca":
        dados["marca"] = texto.strip()
        memoria["etapa"] = "aguardando_modelo"
        return "Perfeito. Agora informe o *modelo do equipamento*."

    if etapa == "aguardando_modelo":
        dados["modelo"] = texto.strip()
        memoria["etapa"] = "aguardando_duvida"
        return "Agora, por favor, descreva *qual é a dúvida*."

    if etapa == "aguardando_duvida":
        dados["duvida"] = texto.strip()
        memoria["etapa"] = "aguardando_defeito"
        return "Certo. Agora informe o *defeito ou situação apresentada*."

    if etapa == "aguardando_defeito":
        dados["defeito"] = texto.strip()
        memoria["etapa"] = "finalizado_suporte"
        return (
            f"✅ *{AGENTE_SUPORTE} | Suporte Técnico TEC9*\n\n"
            "Perfeito. Recebemos seu atendimento técnico.\n\n"
            "Resumo:\n"
            f"- Marca: {dados['marca']}\n"
            f"- Modelo: {dados['modelo']}\n"
            f"- Dúvida: {dados['duvida']}\n"
            f"- Defeito/Situação: {dados['defeito']}\n\n"
            "Nossa equipe técnica irá analisar as informações e dar continuidade ao atendimento."
        )

    if etapa == "finalizado_suporte":
        return (
            f"🔧 *{AGENTE_SUPORTE} | Suporte Técnico TEC9*\n\n"
            "Seu atendimento técnico já foi registrado.\n\n"
            "Se desejar iniciar um novo atendimento, digite *MENU*."
        )

    memoria["etapa"] = "aguardando_marca"
    return (
        f"🔧 *{AGENTE_SUPORTE} | Suporte Técnico TEC9*\n\n"
        "Vamos começar novamente.\n\n"
        "Informe a *marca do equipamento*."
    )

# =========================
# FLUXO ESPECIALISTA
# =========================
def iniciar_fluxo_especialista(memoria):
    memoria["setor"] = "especialista"
    memoria["etapa"] = "aguardando_nome_especialista"
    return (
        f"👤 *{AGENTE_ESPECIALISTA} | Especialista TEC9*\n\n"
        "Vou assumir seu atendimento.\n\n"
        "Para começarmos, por favor informe seu *nome*."
    )

def processar_fluxo_especialista(texto, memoria):
    dados = memoria["dados"]
    etapa = memoria["etapa"]

    if etapa == "aguardando_nome_especialista":
        dados["nome"] = texto.strip()
        memoria["etapa"] = "aguardando_produto_especialista"
        return (
            f"Prazer, *{dados['nome']}*.\n\n"
            "Agora me informe o *produto ou necessidade*."
        )

    if etapa == "aguardando_produto_especialista":
        dados["produto"] = texto.strip()
        memoria["etapa"] = "aguardando_quantidade_especialista"
        return "Perfeito. Agora informe a *quantidade*."

    if etapa == "aguardando_quantidade_especialista":
        dados["quantidade"] = texto.strip()
        memoria["etapa"] = "aguardando_email_especialista"
        return "Agora, por favor, informe seu *email*."

    if etapa == "aguardando_email_especialista":
        email = extrair_email(texto)
        if not email:
            return (
                "Por favor, envie um *email válido* para continuarmos.\n\n"
                "Exemplo: nome@empresa.com.br"
            )

        dados["email"] = email
        memoria["etapa"] = "aguardando_cnpj_especialista"
        return (
            "Se o atendimento for para *empresa*, informe agora o *CNPJ*.\n\n"
            "Caso não tenha CNPJ, responda apenas:\n"
            "*NAO TENHO CNPJ*"
        )

    if etapa == "aguardando_cnpj_especialista":
        texto_norm = normalizar_texto(texto)
        cnpj = extrair_cnpj(texto)

        if cnpj:
            dados["cnpj"] = cnpj
            memoria["etapa"] = "finalizado_especialista"
            return (
                f"✅ *{AGENTE_ESPECIALISTA} | Especialista TEC9*\n\n"
                "Perfeito. Recebemos suas informações.\n\n"
                "Resumo:\n"
                f"- Nome: {dados['nome']}\n"
                f"- Produto/Necessidade: {dados['produto']}\n"
                f"- Quantidade: {dados['quantidade']}\n"
                f"- Email: {dados['email']}\n"
                f"- CNPJ: {dados['cnpj']}\n\n"
                "Seu atendimento foi encaminhado com prioridade."
            )

        if texto_norm in ["nao tenho cnpj", "não tenho cnpj", "nao", "não", "pf", "pessoa fisica", "pessoa física"]:
            memoria["etapa"] = "finalizado_especialista"
            return (
                f"✅ *{AGENTE_ESPECIALISTA} | Especialista TEC9*\n\n"
                "Perfeito. Recebemos suas informações.\n\n"
                "Resumo:\n"
                f"- Nome: {dados['nome']}\n"
                f"- Produto/Necessidade: {dados['produto']}\n"
                f"- Quantidade: {dados['quantidade']}\n"
                f"- Email: {dados['email']}\n\n"
                "Seu atendimento foi encaminhado com prioridade."
            )

        return (
            "Se for atendimento empresarial, envie o *CNPJ*.\n\n"
            "Caso não tenha CNPJ, responda:\n"
            "*NAO TENHO CNPJ*"
        )

    if etapa == "finalizado_especialista":
        return (
            f"👤 *{AGENTE_ESPECIALISTA} | Especialista TEC9*\n\n"
            "Seu atendimento já foi registrado.\n\n"
            "Se desejar iniciar um novo atendimento, digite *MENU*."
        )

    memoria["etapa"] = "aguardando_nome_especialista"
    return (
        f"👤 *{AGENTE_ESPECIALISTA} | Especialista TEC9*\n\n"
        "Vamos começar novamente.\n\n"
        "Por favor, informe seu *nome*."
    )

# =========================
# MOTOR DE CONVERSA
# =========================
def processar_mensagem(numero, texto):
    texto_norm = normalizar_texto(texto)
    memoria = obter_memoria(numero)

    # Comando para voltar ao menu
    if texto_norm in PALAVRAS_REINICIAR or texto_norm in PALAVRAS_MENU:
        limpar_memoria(numero)
        return menu_principal()

    # Se ainda está no menu principal
    if memoria["etapa"] == "menu_principal":
        if texto_norm == "1":
            return iniciar_fluxo_vendas(memoria)

        if texto_norm == "2":
            return iniciar_fluxo_suporte(memoria)

        if texto_norm == "3":
            return iniciar_fluxo_especialista(memoria)

        if cliente_quente(texto_norm):
            memoria["setor"] = "vendas"
            memoria["etapa"] = "aguardando_nome"
            return resposta_cliente_quente()

        return menu_principal()

    # Fluxos com memoria
    if memoria["setor"] == "vendas":
        return processar_fluxo_vendas(texto, memoria)

    if memoria["setor"] == "suporte":
        return processar_fluxo_suporte(texto, memoria)

    if memoria["setor"] == "especialista":
        return processar_fluxo_especialista(texto, memoria)

    limpar_memoria(numero)
    return menu_principal()

# =========================
# ENVIO DE MENSAGEM
# =========================
def responder(numero, texto):
    if not ACCESS_TOKEN:
        print("META_ACCESS_TOKEN nao configurado", flush=True)
        return

    if not PHONE_NUMBER_ID:
        print("PHONE_NUMBER_ID nao configurado", flush=True)
        return

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        print("ENVIADO:", r.status_code, r.text, flush=True)
    except Exception as e:
        print("ERRO AO ENVIAR:", str(e), flush=True)

# =========================
# ROTAS
# =========================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT ONLINE COM MEMORIA 🚀", 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "verify_token_configurado": bool(VERIFY_TOKEN),
        "access_token_configurado": bool(ACCESS_TOKEN),
        "phone_number_id_configurado": bool(PHONE_NUMBER_ID),
        "clientes_em_memoria": len(memoria_clientes)
    }), 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        print("VALIDACAO RECEBIDA", flush=True)
        print("hub.mode:", mode, flush=True)
        print("hub.verify_token:", token, flush=True)

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK VALIDADO COM SUCESSO", flush=True)
            return challenge, 200

        return "Erro de verificacao", 403

    data = request.get_json(silent=True)
    print("WEBHOOK RECEBIDO:", data, flush=True)

    try:
        if not data:
            return jsonify({"status": "no data"}), 200

        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                # Ignora status
                if "statuses" in value:
                    print("STATUS IGNORADO:", value.get("statuses"), flush=True)
                    continue

                # Processa apenas mensagens
                if "messages" not in value:
                    print("Evento ignorado (sem mensagem)", flush=True)
                    continue

                for msg in value.get("messages", []):
                    numero = msg.get("from")
                    tipo = msg.get("type", "")

                    if not numero:
                        print("Mensagem sem remetente, ignorada.", flush=True)
                        continue

                    if tipo == "text":
                        texto = msg.get("text", {}).get("body", "").strip()
                        print(f"MENSAGEM DE {numero}: {texto}", flush=True)

                        resposta = processar_mensagem(numero, texto)
                        responder(numero, resposta)
                    else:
                        print(f"MENSAGEM NAO TEXTO DE {numero}: {tipo}", flush=True)
                        responder(numero, resposta_nao_texto())

    except Exception as e:
        print("ERRO AO PROCESSAR WEBHOOK:", str(e), flush=True)

    return jsonify({"ok": True}), 200

# =========================
# START
# =========================
if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 3000))
    print(f"Servidor iniciando na porta {porta}", flush=True)
    app.run(host="0.0.0.0", port=porta)
