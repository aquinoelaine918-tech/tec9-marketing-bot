import os
import time
from pathlib import Path

import pandas as pd


# =========================================================
# CONFIGURAÇÕES
# =========================================================
ARQUIVO_ENTRADA = os.getenv("ARQUIVO_ENTRADA", "produtos_atualizados.xlsx")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/data"))
ARQUIVO_SAIDA = OUTPUT_DIR / os.getenv("ARQUIVO_SAIDA", "precificacao_automatica.xlsx")

# tolerâncias
TOLERANCIA_COMPETITIVO = float(os.getenv("TOLERANCIA_COMPETITIVO", "3"))   # %
AJUSTE_URGENTE = float(os.getenv("AJUSTE_URGENTE", "10"))                  # %
MARGEM_PADRAO = float(os.getenv("MARGEM_PADRAO", "25"))                    # %

# se quiser manter o container "online" no Railway
MANTER_ATIVO = os.getenv("MANTER_ATIVO", "true").strip().lower() == "true"
TEMPO_ESPERA_SEGUNDOS = int(os.getenv("TEMPO_ESPERA_SEGUNDOS", "3600"))


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================
def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renomeia colunas comuns para um padrão único.
    """
    mapa = {
        "sku": "SKU",
        "SKU": "SKU",

        "produto": "PRODUTO",
        "PRODUTO": "PRODUTO",
        "title": "PRODUTO",

        "custo": "CUSTO",
        "CUSTO": "CUSTO",
        "CUSTO_TRATADO": "CUSTO",

        "preco_venda": "PRECO_VENDA",
        "PRECO_VENDA": "PRECO_VENDA",
        "venda": "PRECO_VENDA",
        "VENDA": "PRECO_VENDA",

        "preco_sugerido": "PRECO_SUGERIDO",
        "PRECO_SUGERIDO": "PRECO_SUGERIDO",

        "margem_%": "MARGEM_%",
        "MARGEM_%": "MARGEM_%",
        "margem": "MARGEM_%",
        "MARGEM": "MARGEM_%",
    }

    novas_colunas = {}
    for col in df.columns:
        col_limpa = str(col).strip()
        if col_limpa in mapa:
            novas_colunas[col] = mapa[col_limpa]
        else:
            novas_colunas[col] = col_limpa

    df = df.rename(columns=novas_colunas)
    return df


def converter_numero(valor):
    """
    Converte textos numéricos brasileiros e gerais para float.
    Exemplos:
    1.350,00 -> 1350.00
    185,9    -> 185.90
    1900     -> 1900.00
    """
    if pd.isna(valor):
        return 0.0

    texto = str(valor).strip()

    if texto == "":
        return 0.0

    texto = texto.replace("R$", "").replace(" ", "")

    # caso brasileiro com milhar e vírgula decimal
    if "." in texto and "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return 0.0


def classificar_status(diferenca_percentual: float) -> str:
    """
    Classifica conforme diferença entre PRECO_VENDA e PRECO_SUGERIDO.
    """
    if abs(diferenca_percentual) <= TOLERANCIA_COMPETITIVO:
        return "COMPETITIVO"
    elif diferenca_percentual > AJUSTE_URGENTE:
        return "ACIMA DO MERCADO"
    elif diferenca_percentual < -AJUSTE_URGENTE:
        return "ABAIXO DO MERCADO"
    elif diferenca_percentual > 0:
        return "ACIMA DO MERCADO"
    else:
        return "ABAIXO DO MERCADO"


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = normalizar_colunas(df)

    print(f"--- Colunas detectadas no arquivo: {list(df.columns)}")

    # colunas obrigatórias mínimas
    obrigatorias = ["SKU", "PRODUTO", "CUSTO"]
    for coluna in obrigatorias:
        if coluna not in df.columns:
            raise Exception(f"ERRO: A coluna '{coluna}' não existe no Excel. Verifique o arquivo!")

    # se não houver PRECO_VENDA, mas houver PRECO_SUGERIDO, usa como venda atual
    if "PRECO_VENDA" not in df.columns:
        if "PRECO_SUGERIDO" in df.columns:
            df["PRECO_VENDA"] = df["PRECO_SUGERIDO"]
        else:
            raise Exception("ERRO: A coluna 'PRECO_VENDA' não existe no Excel. Verifique o arquivo!")

    # margem
    if "MARGEM_%" not in df.columns:
        df["MARGEM_%"] = MARGEM_PADRAO

    # conversões
    df["SKU"] = df["SKU"].astype(str).str.strip()
    df["PRODUTO"] = df["PRODUTO"].astype(str).str.strip()
    df["CUSTO"] = df["CUSTO"].apply(converter_numero)
    df["PRECO_VENDA"] = df["PRECO_VENDA"].apply(converter_numero)
    df["MARGEM_%"] = df["MARGEM_%"].apply(converter_numero)

    # remove linhas sem sku
    df = df[df["SKU"] != ""].copy()

    # remove custo zero
    df = df[df["CUSTO"] > 0].copy()

    return df


def gerar_analise(df: pd.DataFrame) -> pd.DataFrame:
    # se já existir PRECO_SUGERIDO no arquivo, ele será usado como referência
    # se não existir, será calculado pela margem
    if "PRECO_SUGERIDO" in df.columns:
        df["PRECO_SUGERIDO"] = df["PRECO_SUGERIDO"].apply(converter_numero)
        df.loc[df["PRECO_SUGERIDO"] <= 0, "PRECO_SUGERIDO"] = df["CUSTO"] * (
            1 + df["MARGEM_%"] / 100
        )
    else:
        df["PRECO_SUGERIDO"] = df["CUSTO"] * (1 + df["MARGEM_%"] / 100)

    df["DIFERENCA_R$"] = df["PRECO_VENDA"] - df["PRECO_SUGERIDO"]

    df["DIFERENCA_%"] = 0.0
    mask = df["PRECO_SUGERIDO"] > 0
    df.loc[mask, "DIFERENCA_%"] = (
        (df.loc[mask, "PRECO_VENDA"] - df.loc[mask, "PRECO_SUGERIDO"])
        / df.loc[mask, "PRECO_SUGERIDO"]
        * 100
    )

    df["STATUS"] = df["DIFERENCA_%"].apply(classificar_status)

    # ordem final
    colunas_finais = [
        "SKU",
        "PRODUTO",
        "CUSTO",
        "PRECO_VENDA",
        "MARGEM_%",
        "PRECO_SUGERIDO",
        "DIFERENCA_R$",
        "DIFERENCA_%",
        "STATUS",
    ]

    # manter só as que existem
    colunas_finais = [c for c in colunas_finais if c in df.columns]
    df = df[colunas_finais].copy()

    return df


def salvar_excel(df: pd.DataFrame):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(ARQUIVO_SAIDA, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Analise", index=False)

        resumo = pd.DataFrame({
            "Indicador": [
                "TOTAL",
                "COMPETITIVO",
                "ACIMA DO MERCADO",
                "ABAIXO DO MERCADO",
                "URGENTE",
            ],
            "Valor": [
                len(df),
                (df["STATUS"] == "COMPETITIVO").sum(),
                (df["STATUS"] == "ACIMA DO MERCADO").sum(),
                (df["STATUS"] == "ABAIXO DO MERCADO").sum(),
                (df["DIFERENCA_%"].abs() > AJUSTE_URGENTE).sum(),
            ]
        })
        resumo.to_excel(writer, sheet_name="Resumo", index=False)


def imprimir_resumo(df: pd.DataFrame):
    total = len(df)
    competitivo = (df["STATUS"] == "COMPETITIVO").sum()
    acima = (df["STATUS"] == "ACIMA DO MERCADO").sum()
    abaixo = (df["STATUS"] == "ABAIXO DO MERCADO").sum()
    urgente = (df["DIFERENCA_%"].abs() > AJUSTE_URGENTE).sum()

    print("📊 RESUMO:")
    print(f"TOTAL: {total}")
    print(f"COMPETITIVO: {competitivo}")
    print(f"ACIMA: {acima}")
    print(f"ABAIXO: {abaixo}")
    print(f"URGENTE: {urgente}")
    print(f"✅ Arquivo gerado: {ARQUIVO_SAIDA.name}")


def executar():
    df = pd.read_excel(ARQUIVO_ENTRADA)
    df = preparar_dataframe(df)
    df = gerar_analise(df)
    salvar_excel(df)
    imprimir_resumo(df)


# =========================================================
# EXECUÇÃO
# =========================================================
if __name__ == "__main__":
    try:
        executar()

        if MANTER_ATIVO:
            print(f"🟢 Processo concluído. Mantendo container ativo por {TEMPO_ESPERA_SEGUNDOS} segundos...")
            while True:
                time.sleep(TEMPO_ESPERA_SEGUNDOS)

    except Exception as e:
        print(f"❌ {e}")
        raise
