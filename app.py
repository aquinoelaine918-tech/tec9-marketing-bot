import os
import re
import sqlite3
import requests
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIAVEIS DE AMBIENTE
# =========================
VERIFY_TOKEN = (os.getenv("VERIFY_TOKEN") or "").strip()
ACCESS_TOKEN = (os.getenv("META_ACCESS_TOKEN") or "").strip()
PHONE_NUMBER_ID = (os.getenv("PHONE_NUMBER_ID") or "").strip()
WHATSAPP_ALERTA = (os.getenv("WHATSAPP_ALERTA") or "").strip()
FOLLOWUP_TOKEN = (os.getenv("FOLLOWUP_TOKEN") or "").strip()

# =========================
# CONFIGURACOES
# =========================
BASE_BUSCA_SITE = "https://tec9informatica.com.br/busca?q="
AGENTE_VENDAS = "Camila"
AGENTE_SUPORTE = "Lucas"
AGENTE_ESPECIALISTA = "Ricardo"

# Janela para recuperar cliente parado
FOLLOWUP_MINUTOS = 30

# =========================
# BANCO SQLITE
# =========================
conn = sqlite3.connect("tec9_bot.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telefone TEXT NOT NULL,
    nome TEXT,
    produto TEXT,
    quantidade TEXT,
    email TEXT,
    cnpj TEXT,
    setor TEXT,
    origem TEXT,
    status TEXT,
    created_at TEXT,
    updated_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS conversas (
    telefone TEXT PRIMARY KEY,
    setor TEXT,
    etapa TEXT,
    nome TEXT,
    produto TEXT,
    quantidade TEXT,
    email TEXT,
    cnpj TEXT,
    marca TEXT,
    modelo TEXT,
    duvida TEXT,
    defeito TEXT,
    lead_salvo INTEGER DEFAULT 0,
    followup_sent INTEGER DEFAULT 0,
    finalizado INTEGER DEFAULT 0,
    last_interaction TEXT,
    created_at TEXT,
    updated_at TEXT
)
""")

conn.commit()

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

PALAVRAS_PRODUTO = [
    "ssd", "hd", "hdd", "memoria", "memória", "notebook", "monitor",
    "teclado", "mouse", "headset", "gabinete", "fonte", "processador",
    "placa mae", "placa-mãe", "placa mãe", "placa de video", "placa de vídeo",
    "impressora", "toner", "cartucho", "servidor", "switch", "roteador",
    "access point", "nobreak", "webcam", "microfone", "scanner",
    "leitor", "codigo de barras", "código de barras", "gaveta de dinheiro",
    "pdv", "automacao comercial", "automação comercial", "desktop", "pc gamer",
    "all in one", "all-in-one", "mini pc", "estabilizador", "epson",
    "brother", "dell", "lenovo", "hp", "acer", "asus", "logitech",
    "kingston", "crucial", "samsung", "lg", "aoc", "philips", "tplink",
    "tp-link", "intel", "amd", "nvidia"
]

# =========================
# FUNCOES AUXILIARES
# =========================
def agora_iso():
    return datetime.now(timezone.utc).isoformat()

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

def detectar_interesse_produto(texto):
    return contem_palavra(texto, PALAVRAS_PRODUTO)

def montar_link_busca(consulta):
    return f"{BASE_BUSCA_SITE}{quote_plus((consulta or '').strip())}"

def resposta_nao_texto():
    return (
        "Recebemos sua mensagem.\n\n"
        "No momento, para dar continuidade ao atendimento, pedimos por gentileza que envie sua solicitação em formato de texto.\n\n"
        "Digite *OI* para visualizar o menu principal."
    )

# =========================
# CAMADA DE DADOS
# =========================
def iniciar_conversa(numero):
    now = agora_iso()
    cursor.execute("""
        INSERT OR REPLACE INTO conversas (
            telefone, setor, etapa, nome, produto, quantidade, email, cnpj,
            marca, modelo, duvida, defeito, lead_salvo, followup_sent, finalizado,
            last_interaction, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        numero, None, "menu_principal", "", "", "", "", "",
        "", "", "", "", 0, 0, 0, now, now, now
    ))
    conn.commit()

def obter_conversa(numero):
    row = cursor.execute(
        "SELECT * FROM conversas WHERE telefone = ?",
        (numero,)
    ).fetchone()

    if not row:
        iniciar_conversa(numero)
        row = cursor.execute(
            "SELECT * FROM conversas WHERE telefone = ?",
            (numero,)
        ).fetchone()

    return dict(row)

def atualizar_conversa(numero, **campos):
    if not campos:
        return

    campos["updated_at"] = agora_iso()
    campos["last_interaction"] = agora_iso()

    partes = ", ".join([f"{k} = ?" for k in campos.keys()])
    valores = list(campos.values())
    valores.append(numero)

    cursor.execute(
        f"UPDATE conversas SET {partes} WHERE telefone = ?",
        valores
    )
    conn.commit()

def resetar_conversa(numero):
    iniciar_conversa(numero)

def salvar_lead(numero, conversa, origem="bot"):
    now = agora_iso()
    cursor.execute("""
        INSERT INTO leads (
            telefone, nome, produto, quantidade, email, cnpj,
            setor, origem, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        numero,
        conversa.get("nome", ""),
        conversa.get("produto", ""),
        conversa.get("quantidade", ""),
        conversa.get("email", ""),
        conversa.get("cnpj", ""),
        conversa.get("setor", ""),
        origem,
        "novo",
        now,
        now
    ))
    conn.commit()

def enviar_alerta_lead(numero_cliente, conversa):
    if not WHATSAPP_ALERTA:
        print("WHATSAPP_ALERTA nao configurado", flush=True)
        return

    nome = conversa.get("nome") or "Nao informado"
    produto = conversa.get("produto") or "Nao informado"
    quantidade = conversa.get("quantidade") or "Nao informada"
    email = conversa.get("email") or "Nao informado"
    cnpj = conversa.get("cnpj") or "Nao informado"
    setor = conversa.get("setor") or "Nao informado"

    link_cliente = f"https://wa.me/{numero_cliente}"

    mensagem = (
        "🔥 *LEAD QUENTE TEC9*\n\n"
        f"👤 Nome: {nome}\n"
        f"📦 Produto: {produto}\n"
        f"🔢 Quantidade: {quantidade}\n"
        f"📧 Email: {email}\n"
        f"🏢 CNPJ: {cnpj}\n"
        f"📌 Setor: {setor}\n\n"
        "👉 Abrir conversa com o cliente:\n"
        f"{link_cliente}"
    )

    enviar_mensagem(WHATSAPP_ALERTA, mensagem)

# =========================
# ENVIO DE MENSAGEM
# =========================
def enviar_mensagem(numero, texto):
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
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print("ENVIADO:", response.status_code, response.text, flush=True)
    except Exception as e:
        print("ERRO AO ENVIAR:", str(e), flush=True)

# =========================
# TEXTOS
# =========================
def menu_principal():
    return (
        "Olá! Seja bem-vindo(a) à *TEC9 Informática*.\n\n"
        "Você será atendido(a) por nossa equipe especializada:\n\n"
        f"1 - *{AGENTE_VENDAS}* | Orçamentos e Vendas\n"
        f"2 - *{AGENTE_SUPORTE}* | Suporte Técnico\n"
        f"3 - *{AGENTE_ESPECIALISTA}* | Especialista TEC9\n\n"
        "Digite apenas o número da opção desejada."
    )

def resposta_produto(texto):
    link = montar_link_busca(texto)
    return (
        f"💰 *{AGENTE_VENDAS} | Consultora Comercial TEC9*\n\n"
        "Perfeito! Localizei uma busca relacionada ao produto que você procura.\n\n"
        f"👉 {link}\n\n"
        "Para eu te ajudar com mais precisão, digite *1* para orçamento ou me informe seu *nome* para iniciarmos seu atendimento."
    )

def resposta_cliente_quente():
    return (
        f"🔥 *{AGENTE_VENDAS} | Atendimento Comercial Prioritário*\n\n"
        "Perfeito. Vou te atender com prioridade.\n\n"
        "Para começarmos, por favor informe seu *nome*."
    )

# =========================
# FLUXO VENDAS
# =========================
def iniciar_fluxo_vendas(numero):
    atualizar_conversa(
        numero,
        setor="vendas",
        etapa="aguardando_nome",
        followup_sent=0,
        finalizado=0
    )
    return (
        f"💰 *{AGENTE_VENDAS} | Orçamentos e Vendas*\n\n"
        "Vou te ajudar com seu orçamento.\n\n"
        "Para começarmos, por favor informe seu *nome*."
    )

def processar_fluxo_vendas(numero, texto, conversa):
    etapa = conversa.get("etapa", "")
    texto_norm = normalizar_texto(texto)

    if etapa == "aguardando_nome":
        atualizar_conversa(numero, nome=texto.strip(), etapa="aguardando_quantidade")
        return (
            f"Prazer, *{texto.strip()}*.\n\n"
            "Agora, por favor informe a *quantidade desejada*."
        )

    if etapa == "aguardando_quantidade":
        atualizar_conversa(numero, quantidade=texto.strip(), etapa="aguardando_produto")
        return (
            "Perfeito.\n\n"
            "Agora me informe o *nome do produto ou modelo* que você procura."
        )

    if etapa == "aguardando_produto":
        atualizar_conversa(numero, produto=texto.strip(), etapa="aguardando_email")
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

        atualizar_conversa(numero, email=email, etapa="aguardando_cnpj_ou_finalizacao")
        return (
            "Perfeito. Recebemos seu email.\n\n"
            "Se a compra for para *empresa*, informe agora o *CNPJ*.\n\n"
            "Se não for compra empresarial, responda apenas:\n"
            "*NAO TENHO CNPJ*"
        )

    if etapa == "aguardando_cnpj_ou_finalizacao":
        cnpj = extrair_cnpj(texto)

        if cnpj:
            atualizar_conversa(numero, cnpj=cnpj, etapa="finalizado_vendas", finalizado=1)
            conversa_atualizada = obter_conversa(numero)
            if not conversa_atualizada.get("lead_salvo"):
                salvar_lead(numero, conversa_atualizada)
                enviar_alerta_lead(numero, conversa_atualizada)
                atualizar_conversa(numero, lead_salvo=1)

            link = montar_link_busca(conversa_atualizada.get("produto", ""))
            return (
                f"✅ *{AGENTE_VENDAS} | Consultora Comercial TEC9*\n\n"
                "Perfeito. Recebemos suas informações para atendimento corporativo.\n\n"
                "Resumo do atendimento:\n"
                f"- Nome: {conversa_atualizada.get('nome', '')}\n"
                f"- Quantidade: {conversa_atualizada.get('quantidade', '')}\n"
                f"- Produto/Modelo: {conversa_atualizada.get('produto', '')}\n"
                f"- Email: {conversa_atualizada.get('email', '')}\n"
                f"- CNPJ: {conversa_atualizada.get('cnpj', '')}\n\n"
                "Busca relacionada no site:\n"
                f"👉 {link}\n\n"
                "Sua solicitação foi encaminhada para análise comercial.\n"
                "Em breve daremos continuidade com a proposta."
            )

        if texto_norm in ["nao tenho cnpj", "não tenho cnpj", "nao", "não", "pf", "pessoa fisica", "pessoa física"]:
            atualizar_conversa(numero, cnpj="", etapa="finalizado_vendas", finalizado=1)
            conversa_atualizada = obter_conversa(numero)
            if not conversa_atualizada.get("lead_salvo"):
                salvar_lead(numero, conversa_atualizada)
                enviar_alerta_lead(numero, conversa_atualizada)
                atualizar_conversa(numero, lead_salvo=1)

            link = montar_link_busca(conversa_atualizada.get("produto", ""))
            return (
                f"✅ *{AGENTE_VENDAS} | Consultora Comercial TEC9*\n\n"
                "Perfeito. Recebemos suas informações.\n\n"
                "Resumo do atendimento:\n"
                f"- Nome: {conversa_atualizada.get('nome', '')}\n"
                f"- Quantidade: {conversa_atualizada.get('quantidade', '')}\n"
                f"- Produto/Modelo: {conversa_atualizada.get('produto', '')}\n"
                f"- Email: {conversa_atualizada.get('email', '')}\n\n"
                "Busca relacionada no site:\n"
                f"👉 {link}\n\n"
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

    atualizar_conversa(numero, etapa="aguardando_nome")
    return (
        f"💰 *{AGENTE_VENDAS} | Orçamentos e Vendas*\n\n"
        "Vamos começar novamente.\n\n"
        "Por favor, informe seu *nome*."
    )

# =========================
# FLUXO SUPORTE
# =========================
def iniciar_fluxo_suporte(numero):
    atualizar_conversa(
        numero,
        setor="suporte",
        etapa="aguardando_marca",
        followup_sent=0,
        finalizado=0
    )
    return (
        f"🔧 *{AGENTE_SUPORTE} | Suporte Técnico TEC9*\n\n"
        "Vou dar sequência ao seu atendimento.\n\n"
        "Para começarmos, informe a *marca do equipamento*."
    )

def processar_fluxo_suporte(numero, texto, conversa):
    etapa = conversa.get("etapa", "")

    if etapa == "aguardando_marca":
        atualizar_conversa(numero, marca=texto.strip(), etapa="aguardando_modelo")
        return "Perfeito. Agora informe o *modelo do equipamento*."

    if etapa == "aguardando_modelo":
        atualizar_conversa(numero, modelo=texto.strip(), etapa="aguardando_duvida")
        return "Agora, por favor, descreva *qual é a dúvida*."

    if etapa == "aguardando_duvida":
        atualizar_conversa(numero, duvida=texto.strip(), etapa="aguardando_defeito")
        return "Certo. Agora informe o *defeito ou situação apresentada*."

    if etapa == "aguardando_defeito":
        atualizar_conversa(numero, defeito=texto.strip(), etapa="finalizado_suporte", finalizado=1)
        conversa_atualizada = obter_conversa(numero)
        return (
            f"✅ *{AGENTE_SUPORTE} | Suporte Técnico TEC9*\n\n"
            "Perfeito. Recebemos seu atendimento técnico.\n\n"
            "Resumo:\n"
            f"- Marca: {conversa_atualizada.get('marca', '')}\n"
            f"- Modelo: {conversa_atualizada.get('modelo', '')}\n"
            f"- Dúvida: {conversa_atualizada.get('duvida', '')}\n"
            f"- Defeito/Situação: {conversa_atualizada.get('defeito', '')}\n\n"
            "Nossa equipe técnica irá analisar as informações e dar continuidade ao atendimento."
        )

    if etapa == "finalizado_suporte":
        return (
            f"🔧 *{AGENTE_SUPORTE} | Suporte Técnico TEC9*\n\n"
            "Seu atendimento técnico já foi registrado.\n\n"
            "Se desejar iniciar um novo atendimento, digite *MENU*."
        )

    atualizar_conversa(numero, etapa="aguardando_marca")
    return (
        f"🔧 *{AGENTE_SUPORTE} | Suporte Técnico TEC9*\n\n"
        "Vamos começar novamente.\n\n"
        "Informe a *marca do equipamento*."
    )

# =========================
# FLUXO ESPECIALISTA
# =========================
def iniciar_fluxo_especialista(numero):
    atualizar_conversa(
        numero,
        setor="especialista",
        etapa="aguardando_nome_especialista",
        followup_sent=0,
        finalizado=0
    )
    return (
        f"👤 *{AGENTE_ESPECIALISTA} | Especialista TEC9*\n\n"
        "Vou assumir seu atendimento.\n\n"
        "Para começarmos, por favor informe seu *nome*."
    )

def processar_fluxo_especialista(numero, texto, conversa):
    etapa = conversa.get("etapa", "")
    texto_norm = normalizar_texto(texto)

    if etapa == "aguardando_nome_especialista":
        atualizar_conversa(numero, nome=texto.strip(), etapa="aguardando_produto_especialista")
        return (
            f"Prazer, *{texto.strip()}*.\n\n"
            "Agora me informe o *produto ou necessidade*."
        )

    if etapa == "aguardando_produto_especialista":
        atualizar_conversa(numero, produto=texto.strip(), etapa="aguardando_quantidade_especialista")
        return "Perfeito. Agora informe a *quantidade*."

    if etapa == "aguardando_quantidade_especialista":
        atualizar_conversa(numero, quantidade=texto.strip(), etapa="aguardando_email_especialista")
        return "Agora, por favor, informe seu *email*."

    if etapa == "aguardando_email_especialista":
        email = extrair_email(texto)
        if not email:
            return (
                "Por favor, envie um *email válido* para continuarmos.\n\n"
                "Exemplo: nome@empresa.com.br"
            )

        atualizar_conversa(numero, email=email, etapa="aguardando_cnpj_especialista")
        return (
            "Se o atendimento for para *empresa*, informe agora o *CNPJ*.\n\n"
            "Caso não tenha CNPJ, responda apenas:\n"
            "*NAO TENHO CNPJ*"
        )

    if etapa == "aguardando_cnpj_especialista":
        cnpj = extrair_cnpj(texto)

        if cnpj:
            atualizar_conversa(numero, cnpj=cnpj, etapa="finalizado_especialista", finalizado=1)
            conversa_atualizada = obter_conversa(numero)
            if not conversa_atualizada.get("lead_salvo"):
                salvar_lead(numero, conversa_atualizada)
                enviar_alerta_lead(numero, conversa_atualizada)
                atualizar_conversa(numero, lead_salvo=1)

            return (
                f"✅ *{AGENTE_ESPECIALISTA} | Especialista TEC9*\n\n"
                "Perfeito. Recebemos suas informações.\n\n"
                "Seu atendimento foi encaminhado com prioridade."
            )

        if texto_norm in ["nao tenho cnpj", "não tenho cnpj", "nao", "não", "pf", "pessoa fisica", "pessoa física"]:
            atualizar_conversa(numero, cnpj="", etapa="finalizado_especialista", finalizado=1)
            conversa_atualizada = obter_conversa(numero)
            if not conversa_atualizada.get("lead_salvo"):
                salvar_lead(numero, conversa_atualizada)
                enviar_alerta_lead(numero, conversa_atualizada)
                atualizar_conversa(numero, lead_salvo=1)

            return (
                f"✅ *{AGENTE_ESPECIALISTA} | Especialista TEC9*\n\n"
                "Perfeito. Recebemos suas informações.\n\n"
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

    atualizar_conversa(numero, etapa="aguardando_nome_especialista")
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
    conversa = obter_conversa(numero)

    if texto_norm in PALAVRAS_REINICIAR or texto_norm in PALAVRAS_MENU:
        resetar_conversa(numero)
        return menu_principal()

    if conversa.get("etapa") == "menu_principal":
        if texto_norm == "1":
            return iniciar_fluxo_vendas(numero)

        if texto_norm == "2":
            return iniciar_fluxo_suporte(numero)

        if texto_norm == "3":
            return iniciar_fluxo_especialista(numero)

        if cliente_quente(texto_norm):
            atualizar_conversa(numero, setor="vendas", etapa="aguardando_nome", followup_sent=0, finalizado=0)
            return resposta_cliente_quente()

        if detectar_interesse_produto(texto_norm):
            return resposta_produto(texto)

        return menu_principal()

    conversa = obter_conversa(numero)

    if conversa.get("setor") == "vendas":
        return processar_fluxo_vendas(numero, texto, conversa)

    if conversa.get("setor") == "suporte":
        return processar_fluxo_suporte(numero, texto, conversa)

    if conversa.get("setor") == "especialista":
        return processar_fluxo_especialista(numero, texto, conversa)

    resetar_conversa(numero)
    return menu_principal()

# =========================
# RECUPERACAO AUTOMATICA
# =========================
def buscar_conversas_para_followup():
    limite = (datetime.now(timezone.utc) - timedelta(minutes=FOLLOWUP_MINUTOS)).isoformat()

    rows = cursor.execute("""
        SELECT * FROM conversas
        WHERE finalizado = 0
          AND followup_sent = 0
          AND etapa != 'menu_principal'
          AND last_interaction <= ?
    """, (limite,)).fetchall()

    return [dict(r) for r in rows]

def mensagem_followup(conversa):
    nome = conversa.get("nome") or "Tudo bem"
    setor = conversa.get("setor") or ""

    if setor == "vendas":
        return (
            f"Olá, *{nome}*! Aqui é a *{AGENTE_VENDAS}* da *TEC9 Informática*.\n\n"
            "Percebi que seu atendimento comercial ficou em andamento.\n"
            "Se desejar, podemos continuar seu orçamento por aqui.\n\n"
            "Basta me enviar a próxima informação para seguirmos."
        )

    if setor == "suporte":
        return (
            f"Olá, *{nome}*! Aqui é o *{AGENTE_SUPORTE}* da *TEC9 Informática*.\n\n"
            "Vi que seu atendimento técnico ficou em aberto.\n"
            "Se desejar, pode continuar por aqui que eu dou sequência ao suporte."
        )

    if setor == "especialista":
        return (
            f"Olá, *{nome}*! Aqui é o *{AGENTE_ESPECIALISTA}* da *TEC9 Informática*.\n\n"
            "Seu atendimento ficou em andamento.\n"
            "Se desejar, pode continuar por aqui que seguimos com prioridade."
        )

    return (
        "Olá! Aqui é a equipe da *TEC9 Informática*.\n\n"
        "Seu atendimento ficou em andamento.\n"
        "Se desejar, pode continuar por aqui."
    )

def executar_followup():
    conversas = buscar_conversas_para_followup()
    enviados = 0

    for conversa in conversas:
        telefone = conversa["telefone"]
        texto = mensagem_followup(conversa)
        enviar_mensagem(telefone, texto)
        atualizar_conversa(telefone, followup_sent=1)
        enviados += 1

    return enviados

# =========================
# ROTAS
# =========================
@app.route("/", methods=["GET"])
def home():
    return "TEC9 BOT MAQUINA DE VENDAS 🚀", 200

@app.route("/health", methods=["GET"])
def health():
    total_conversas = cursor.execute("SELECT COUNT(*) AS total FROM conversas").fetchone()["total"]
    total_leads = cursor.execute("SELECT COUNT(*) AS total FROM leads").fetchone()["total"]

    return jsonify({
        "status": "online",
        "verify_token_configurado": bool(VERIFY_TOKEN),
        "access_token_configurado": bool(ACCESS_TOKEN),
        "phone_number_id_configurado": bool(PHONE_NUMBER_ID),
        "whatsapp_alerta_configurado": bool(WHATSAPP_ALERTA),
        "followup_token_configurado": bool(FOLLOWUP_TOKEN),
        "conversas": total_conversas,
        "leads": total_leads
    }), 200

@app.route("/followup", methods=["GET", "POST"])
def followup():
    token_recebido = (request.args.get("token") or request.headers.get("X-FOLLOWUP-TOKEN") or "").strip()

    if not FOLLOWUP_TOKEN or token_recebido != FOLLOWUP_TOKEN:
        return jsonify({"ok": False, "erro": "nao autorizado"}), 403

    enviados = executar_followup()
    return jsonify({"ok": True, "followups_enviados": enviados}), 200

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

                if "statuses" in value:
                    print("STATUS IGNORADO:", value.get("statuses"), flush=True)
                    continue

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
                        enviar_mensagem(numero, resposta)
                    else:
                        print(f"MENSAGEM NAO TEXTO DE {numero}: {tipo}", flush=True)
                        enviar_mensagem(numero, resposta_nao_texto())

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
