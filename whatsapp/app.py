@app.route("/webhook", methods=["POST"])
def receber_mensagem():

    data = request.get_json()

    print("EVENTO RECEBIDO:")
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

            print(f"TIPO: {tipo} DE: {numero}")

            if tipo == "text":

                texto = message["text"]["body"].strip()

                print(f"MENSAGEM DE {numero}: {texto}")

                # MENU INICIAL
                if texto.lower() in ["oi", "olá", "ola", "menu", "inicio", "início"]:

                    resposta = """
Olá, seja bem-vindo à TEC9 Informática 🚀

Para iniciarmos seu atendimento, selecione uma opção:

1️⃣ Pessoa Jurídica
2️⃣ Pessoa Física

Digite o número correspondente 👇
"""

                    responder_mensagem(numero, resposta)

                # PESSOA JURÍDICA
                elif texto == "1":

                    resposta = """
🏢 Atendimento Pessoa Jurídica

Para agilizar seu orçamento e atendimento corporativo, envie:

📌 CNPJ
📌 Nome do comprador/responsável
📌 E-mail corporativo
📌 Produto ou solução desejada
📌 Quantidade
📌 Cidade/UF para entrega

Após o envio, nossa equipe comercial dará continuidade ao atendimento 🚀
"""

                    responder_mensagem(numero, resposta)

                # PESSOA FÍSICA
                elif texto == "2":

                    resposta = """
👤 Atendimento Pessoa Física

Para prosseguirmos com seu atendimento, envie:

📌 Nome
📌 Produto desejado
📌 Quantidade
📌 Cidade/UF para entrega
📌 E-mail para envio da proposta (opcional)

Após o envio, nossa equipe comercial dará continuidade ao atendimento 🚀
"""

                    responder_mensagem(numero, resposta)

                else:

                    resposta = """
❌ Opção inválida.

Digite:

1️⃣ Pessoa Jurídica
2️⃣ Pessoa Física
"""

                    responder_mensagem(numero, resposta)

    except Exception as erro:

        print("ERRO AO PROCESSAR:")
        print(erro)

    return "ok", 200
