from flask import Flask, request
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

        mensagem = f"🔎 Encontrei opções para: *{texto_cliente}*\n\n"

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
            f"🔎 Não encontrei p
