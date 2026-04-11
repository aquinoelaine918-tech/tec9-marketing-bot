import os
import re
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIAVEIS DE AMBIENTE
# =========================
VERIFY_TOKEN = (os.getenv("VERIFY_TOKEN") or "").strip()
ACCESS_TOKEN = (os.getenv("META_ACCESS_TOKEN") or "").strip()
PHONE_NUMBER_ID = (os.getenv("PHONE_NUMBER_ID") or "").strip()
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()

# =========================
# AGENTES
# =========================
AGENTE_VENDAS = "Camila"
AGENTE_SUPORTE = "Lucas"
AGENTE_ESPECIALISTA = "Ricardo"

# =========================
# MEMORIA EM RAM
# =========================
memoria_clientes = {}

# =========================
# PALAVRAS-CHAVE
# =========================
PALAVRAS_MENU = ["oi", "olá", "ola", "menu", "inicio", "início", "bom dia", "boa tarde", "boa noite"]
PALAVRAS_REINICIAR = ["menu", "inicio", "início", "reiniciar", "recomeçar", "voltar", "sair"]
PALAVRAS_CLIENTE_QUENTE = ["preco", "preço", "valor", "quanto custa", "orcamento", "orçamento", "comprar"]

# =========================
# FUNCOES AUXILIARES
# =========================
def normalizar_texto(texto):
    return texto.strip().lower() if texto else ""

def extrair_email(texto):
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', texto)
    return match.group(0) if match else None

def extrair_cnpj(texto):
    match = re.search(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', texto)
    return match.group(0) if match else None

def contem_palavra(texto, palavras):
    texto_norm = normalizar_texto(texto)
    return any(p in texto_norm for p in palavras)

def iniciar_memoria(numero):
    memoria_clientes[numero] = {
        "setor": None, "etapa": "menu_principal",
        "dados": {"nome": "", "quantidade": "", "produto": "", "email": "", "cnpj": ""}
    }

def obter_memoria(numero):
    if numero not in memoria_clientes: iniciar_memoria(numero)
    return memoria_clientes[numero]

def limpar_memoria(numero): iniciar_memoria(numero)

def menu_principal():
    return (
        "Olá! Seja bem-vindo(a) à *TEC9 Informática*.\n\n"
        "Escolha uma opção:\n"
        f"1 - *{AGENTE_VENDAS}* | Vendas\n"
        f"2 - *{AGENTE_SUPORTE}* | Suporte\n"
        f"3 - *{AGENTE_ESPECIALISTA}* | Especialista\n\n"
        "Digite o número desejado."
    )

# =========================
# OPENAI (CORRIGIDO PARA GPT-4o)
# =========================
def chamar_openai_vendas(mensagem_cliente, memoria):
    if not OPENAI_API_KEY: return None
    dados = memoria["dados"]
    prompt_sistema = f"Você é {AGENTE_VENDAS}, vendedora da TEC9. Dados atuais: {dados}. Seja cordial e objetiva."
    
    payload = {
        "model": "gpt-4o", # Alterado de gpt-5 para gpt-4o
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": mensagem_cliente}
        ],
        "temperature": 0.7
    }
    
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post("https://openai.com", headers=headers, json=payload, timeout=30)
        return response.json()["choices"][0]["message"]["content"].strip()
    except: return None

# =========================
# FLUXOS
# =========================
def iniciar_fluxo_vendas(memoria):
    memoria["setor"] = "vendas"
    memoria["etapa"] = "aguardando_nome"
    return f"💰 *{AGENTE_VENDAS}* | Olá! Para começar, qual seu *nome*?"

def processar_fluxo_vendas(texto, memoria):
    etapa = memoria["etapa"]
    if etapa == "aguardando_nome":
        memoria["dados"]["nome"] = texto
        memoria["etapa"] = "aguardando_produto"
        return f"Prazer {texto}! O que você procura hoje?"
    return "Entendido. Um consultor entrará em contato."

# =========================
# MOTOR DE CONVERSA
# =========================
def processar_mensagem(numero, texto):
    texto_norm = normalizar_texto(texto)
    memoria = obter_memoria(numero)

    if texto_norm in PALAVRAS_REINICIAR:
        limpar_memoria(numero)
        return menu_principal()

    if memoria["etapa"] == "menu_principal":
        if texto_norm == "1": return iniciar_fluxo_vendas(memoria)
        return menu_principal()

    if memoria["setor"] == "vendas": return processar_fluxo_vendas(texto, memoria)
    return menu_principal()

# =========================
# ENVIO DE MENSAGEM (URL ATUALIZADA)
# =========================
def responder(numero, texto):
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID: return
    # Versão v19.0 é a mais recomendada para estabilidade
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": numero, "type": "text", "text": {"body": texto}}
    
    try:
        requests.post(url, json=payload, headers=headers, timeout=20)
    except Exception as e:
        print(f"Erro envio: {e}")

# =========================
# ROTAS (WEBHOOK)
# =========================
@app.route("/", methods=["GET"])
def home(): return "Bot Online", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Erro de verificacao", 403

    data = request.get_json(silent=True)
    try:
        if data:
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for msg in value.get("messages", []):
                        numero = msg.get("from")
                        if msg.get("type") == "text":
                            texto = msg.get("text", {}).get("body", "")
                            resposta = processar_mensagem(numero, texto)
                            responder(numero, resposta)
    except: pass
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
