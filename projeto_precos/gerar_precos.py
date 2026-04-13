import re
import time
import math
from statistics import mean
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


ARQUIVO_ENTRADA = "produtos_atualizados.xlsx"
ARQUIVO_SAIDA = "comparacao_mercado.xlsx"

USER_AGENT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36"
}

TOLERANCIA_COMPETITIVO = 3.0
PAUSA_ENTRE_BUSCAS = 2.0
LIMITE_PRODUTOS_TESTE = 20  # altere depois


def converter_numero(valor):
    if pd.isna(valor):
        return 0.0

    texto = str(valor).strip()
    if texto == "":
        return 0.0

    texto = texto.replace("R$", "").replace(" ", "")

    if "." in texto and "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return 0.0


def normalizar_texto(texto):
    if not texto:
        return ""
    texto = str(texto).strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def extrair_precos_mercadolivre(termo_busca, limite=5):
    """
    Busca no Mercado Livre e tenta extrair alguns preços visíveis.
    """
    url = f"https://lista.mercadolivre.com.br/{requests.utils.quote(termo_busca)}"

    try:
        resp = requests.get(url, headers=USER_AGENT, timeout=20)
        resp.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "lxml")

    precos = []

    # Mercado Livre costuma usar fração inteira e centavos em spans separados
    inteiros = soup.select(".andes-money-amount__fraction")
    centavos = soup.select(".andes-money-amount__cents")

    # Monta pares quando possível
    for i, inteiro_tag in enumerate(inteiros[:limite]):
        inteiro = inteiro_tag.get_text(strip=True)
        cent = "00"
        if i < len(centavos):
            cent = centavos[i].get_text(strip=True)

        try:
            valor = float(f"{inteiro}.{cent}".replace(".", "").replace(",", "."))
        except Exception:
            try:
                valor = float(inteiro.replace(".", "").replace(",", "."))
            except Exception:
                continue

        if valor > 0:
            precos.append(valor)

    # fallback simples
    precos = [p for p in precos if p > 0]
    return precos[:limite]


def extrair_precos_google_shopping(termo_busca, limite=5):
    """
    Busca simples no Google Shopping via página de pesquisa.
    É um MVP e pode exigir ajuste depois.
    """
    url = f"https://www.google.com/search?tbm=shop&q={requests.utils.quote(termo_busca)}"

    try:
        resp = requests.get(url, headers=USER_AGENT, timeout=20)
        resp.raise_for_status()
    except Exception:
        return []

    html = resp.text

    # tenta achar padrões de preço em R$
    encontrados = re.findall(r'R\$\s?([\d\.\,]+)', html)

    precos = []
    for item in encontrados:
        valor = converter_numero(item)
        if valor > 0:
            precos.append(valor)

    # remove outliers absurdos muito baixos ou repetição excessiva simples
    precos = [p for p in precos if p > 5]
    return precos[:limite]


def buscar_precos_mercado(produto, sku):
    """
    Estratégia:
    1. tenta SKU primeiro
    2. se fraco, tenta nome do produto
    """
    consultas = []

    sku = normalizar_texto(sku)
    produto = normalizar_texto(produto)

    if sku:
        consultas.append(sku)
    if produto:
        consultas.append(produto)

    todos_precos = []
    fontes = []

    for consulta in consultas:
        ml = extrair_precos_mercadolivre(consulta, limite=5)
        if ml:
            todos_precos.extend(ml)
            fontes.append(f"ML:{consulta}")

        google = extrair_precos_google_shopping(consulta, limite=5)
        if google:
            todos_precos.extend(google)
            fontes.append(f"GOOGLE:{consulta}")

        if len(todos_precos) >= 4:
            break

        time.sleep(PAUSA_ENTRE_BUSCAS)

    # limpeza básica
    todos_precos = [p for p in todos_precos if p > 0]

    if not todos_precos:
        return {
            "PRECO_MERCADO_MIN": 0.0,
            "PRECO_MERCADO_MEDIO": 0.0,
            "QTD_PRECOS_COLETADOS": 0,
            "FONTES_BUSCA": ""
        }

    return {
        "PRECO_MERCADO_MIN": min(todos_precos),
        "PRECO_MERCADO_MEDIO": mean(todos_precos),
        "QTD_PRECOS_COLETADOS": len(todos_precos),
        "FONTES_BUSCA": " | ".join(fontes)
    }


def classificar(preco_venda, preco_medio):
    if preco_medio <= 0:
        return "SEM REFERENCIA"

    diff_pct = ((preco_venda - preco_medio) / preco_medio) * 100

    if abs(diff_pct) <= TOLERANCIA_COMPETITIVO:
        return "COMPETITIVO"
    elif diff_pct > TOLERANCIA_COMPETITIVO:
        return "ACIMA DO MERCADO"
    else:
        return "ABAIXO DO MERCADO"


def sugestao_preco(custo, preco_medio):
    """
    Sugestão simples:
    - tenta ficar levemente abaixo da média do mercado
    - nunca abaixo do custo
    """
    if preco_medio <= 0:
        return 0.0

    sugerido = preco_medio * 0.98
    if sugerido < custo:
        sugerido = custo * 1.10

    return round(sugerido, 2)


def main():
    df = pd.read_excel(ARQUIVO_ENTRADA)

    # normalização de colunas
    mapa = {
        "sku": "SKU",
        "produto": "PRODUTO",
        "title": "PRODUTO",
        "custo": "CUSTO",
        "preco_venda": "PRECO_VENDA",
        "venda": "PRECO_VENDA",
        "preco_sugerido": "PRECO_VENDA",
    }

    df = df.rename(columns={col: mapa.get(str(col).strip().lower(), col) for col in df.columns})

    obrigatorias = ["SKU", "PRODUTO", "CUSTO"]
    for col in obrigatorias:
        if col not in df.columns:
            raise Exception(f"Coluna obrigatória ausente: {col}")

    if "PRECO_VENDA" not in df.columns:
        df["PRECO_VENDA"] = 0.0

    df["SKU"] = df["SKU"].astype(str).str.strip()
    df["PRODUTO"] = df["PRODUTO"].astype(str).str.strip()
    df["CUSTO"] = df["CUSTO"].apply(converter_numero)
    df["PRECO_VENDA"] = df["PRECO_VENDA"].apply(converter_numero)

    df = df[df["SKU"] != ""].copy()
    df = df[df["CUSTO"] > 0].copy()

    # teste inicial limitado
    df = df.head(LIMITE_PRODUTOS_TESTE).copy()

    resultados = []

    for i, row in df.iterrows():
        sku = row["SKU"]
        produto = row["PRODUTO"]
        custo = row["CUSTO"]
        preco_venda = row["PRECO_VENDA"]

        print(f"Buscando mercado: {sku} | {produto}")

        mercado = buscar_precos_mercado(produto, sku)

        preco_medio = mercado["PRECO_MERCADO_MEDIO"]
        preco_min = mercado["PRECO_MERCADO_MIN"]

        status = classificar(preco_venda, preco_medio) if preco_venda > 0 else "SEM PRECO_INTERNO"
        preco_sugerido_novo = sugestao_preco(custo, preco_medio)

        diff_mercado_pct = 0.0
        if preco_medio > 0 and preco_venda > 0:
            diff_mercado_pct = ((preco_venda - preco_medio) / preco_medio) * 100

        resultados.append({
            "SKU": sku,
            "PRODUTO": produto,
            "CUSTO": custo,
            "PRECO_VENDA": preco_venda,
            "PRECO_MERCADO_MIN": preco_min,
            "PRECO_MERCADO_MEDIO": round(preco_medio, 2) if preco_medio > 0 else 0.0,
            "DIFERENCA_MERCADO_%": round(diff_mercado_pct, 2),
            "STATUS_MERCADO": status,
            "PRECO_SUGERIDO_NOVO": preco_sugerido_novo,
            "QTD_PRECOS_COLETADOS": mercado["QTD_PRECOS_COLETADOS"],
            "FONTES_BUSCA": mercado["FONTES_BUSCA"],
        })

        time.sleep(PAUSA_ENTRE_BUSCAS)

    df_resultado = pd.DataFrame(resultados)

    with pd.ExcelWriter(ARQUIVO_SAIDA, engine="openpyxl") as writer:
        df_resultado.to_excel(writer, sheet_name="Comparacao Mercado", index=False)

        resumo = pd.DataFrame({
            "Indicador": [
                "TOTAL ANALISADO",
                "COMPETITIVO",
                "ACIMA DO MERCADO",
                "ABAIXO DO MERCADO",
                "SEM REFERENCIA",
                "SEM PRECO_INTERNO",
            ],
            "Valor": [
                len(df_resultado),
                (df_resultado["STATUS_MERCADO"] == "COMPETITIVO").sum(),
                (df_resultado["STATUS_MERCADO"] == "ACIMA DO MERCADO").sum(),
                (df_resultado["STATUS_MERCADO"] == "ABAIXO DO MERCADO").sum(),
                (df_resultado["STATUS_MERCADO"] == "SEM REFERENCIA").sum(),
                (df_resultado["STATUS_MERCADO"] == "SEM PRECO_INTERNO").sum(),
            ]
        })
        resumo.to_excel(writer, sheet_name="Resumo", index=False)

    print("\n✅ Comparação com mercado concluída.")
    print(f"📁 Arquivo gerado: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
