"""
MÓDULO 3 · AGRUPAMENTOS E TOTAIS — groupby + gráficos
Análise de Dados — Módulo 3

Agora que tudo está em UMA tabela (saida/modulo3/cruzamento.xlsx), a análise
vira um padrão novo, porém igualmente simples:

    ler o cruzamento  →  groupby por categoria  →  somar/média/contar  →  salvar + gráfico.

    python3 scripts/modulo3/m3_agrupamentos.py

Lê   : saida/modulo3/cruzamento.xlsx   (gerado por m3_cruzamento.py)
Grava: saida/modulo3/agrupamentos_*.xlsx  +  saida/modulo3/graficos/*.png

------------------------------------------------------------------------
PENSAMENTO COMPUTACIONAL AQUI:
  • Decomposição → cada pergunta (soma, média, contagem) é um groupby separado.
  • Padrões      → "agrupar por X, agregar por Y" — só mudam X e Y.
  • Abstração    → o groupby abstrai o "para cada município/secretaria/região".
  • Algoritmo    → agrupar → agregar → conferir → salvar .xlsx + salvar .png.
------------------------------------------------------------------------
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent.parent
ENTRADA = RAIZ / "saida" / "modulo3" / "cruzamento.xlsx"
SAIDA_DIR = RAIZ / "saida" / "modulo3"
GRAFICOS = SAIDA_DIR / "graficos"

plt.rcParams["figure.figsize"] = (8, 5)


def carregar() -> pd.DataFrame:
    if not ENTRADA.exists():
        raise SystemExit(
            f"Não achei {ENTRADA.relative_to(RAIZ)}.\n"
            "Rode antes:  python3 scripts/modulo3/m3_cruzamento.py"
        )
    return pd.read_excel(ENTRADA)


def salvar(df: pd.DataFrame, nome: str) -> None:
    destino = SAIDA_DIR / f"agrupamentos_{nome}.xlsx"
    df.to_excel(destino, index=False)
    print(f"  [xlsx] {destino.relative_to(RAIZ)}  ({len(df)} linhas)")


def grafico_barras(df: pd.DataFrame, col_x: str, col_y: str,
                   titulo: str, nome_png: str) -> None:
    fig, ax = plt.subplots()
    ax.barh(df[col_x].astype(str), df[col_y], color="#2E7D32")
    ax.set_xlabel(col_y)
    ax.set_title(titulo)
    fig.tight_layout()
    destino = GRAFICOS / f"{nome_png}.png"
    fig.savefig(destino, dpi=120)
    plt.close(fig)
    print(f"  [png]  {destino.relative_to(RAIZ)}")


def grafico_pizza(conts: pd.Series, titulo: str, nome_png: str) -> None:
    fig, ax = plt.subplots()
    ax.pie(conts.values, labels=conts.index.astype(str), autopct="%1.0f%%",
           startangle=90)
    ax.set_title(titulo)
    ax.axis("equal")
    fig.tight_layout()
    destino = GRAFICOS / f"{nome_png}.png"
    fig.savefig(destino, dpi=120)
    plt.close(fig)
    print(f"  [png]  {destino.relative_to(RAIZ)}")


# ==========================================================================
# 1) SOMAS por município
# ==========================================================================
def somas_por_municipio(df: pd.DataFrame) -> None:
    """Total de matrículas e remuneração por município."""
    print("\n[1] SOMAS por município")
    agg = (df.groupby("Município")
             .agg(Matriculas=("Matrículas", "sum"),
                  Remuneracao=("Remuneração", "sum"),
                  Escolas=("CNPJ_Escola", "nunique"))
             .reset_index()
             .sort_values("Matriculas", ascending=False))
    salvar(agg, "soma_municipio")
    top = agg.head(10).sort_values("Matriculas")
    grafico_barras(top, "Município", "Matriculas",
                   "Total de matrículas por município (top 10)",
                   "agrup_barras_matriculas_municipio")


# ==========================================================================
# 2) MÉDIAS por região
# ==========================================================================
def medias_por_regiao(df: pd.DataFrame) -> None:
    """Remuneração e matrícula médias por região do estado."""
    print("\n[2] MÉDIAS por região")
    agg = (df.groupby("Região")
             .agg(Remuneracao_media=("Remuneração", "mean"),
                  Matricula_media=("Matrículas", "mean"),
                  Populacao_media=("População", "mean"))
             .round(2)
             .reset_index())
    salvar(agg, "media_regiao")
    grafico_pizza(df["Região"].value_counts(),
                  "Servidores por região", "agrup_pizza_regiao")


# ==========================================================================
# 3) CONTAGENS por secretaria/dependência
# ==========================================================================
def contagens_por_dependencia(df: pd.DataFrame) -> None:
    """Contagem de escolas e servidores por dependência administrativa."""
    print("\n[3] CONTAGENS por dependência")
    agg = (df.groupby("Dependência")
             .agg(Escolas=("CNPJ_Escola", "nunique"),
                  Servidores=("CPF", "nunique"))
             .reset_index())
    salvar(agg, "contagem_dependencia")
    grafico_barras(agg.sort_values("Servidores"),
                   "Dependência", "Servidores",
                   "Servidores por dependência administrativa",
                   "agrup_barras_servidores_dependencia")


# ==========================================================================
# >>> EXERCÍCIO DOS ALUNOS <<<
# --------------------------------------------------------------------------
# Invente uma MÉTRICA NOVA e um novo agrupamento. Ideias:
#   • "alunos por servidor" por município = Matrículas / contagem de CPF.
#   • Remuneração média por cargo, agrupando por Cargo.
#   • Escolas por situacao (Ativa/Extinta/Paralisada) por região.
#
# Dica de prompt:
#   "Crie um groupby em pandas que calcule Matrículas dividido pelo número
#    distinto de CPFs, por município, e ordene do maior para o menor."
# Implemente uma função nova seguindo o PADRÃO acima e chame-a no main().
# ==========================================================================


def main() -> None:
    df = carregar()
    print(f"carregado: {len(df)} linhas, {len(df.columns)} colunas")
    GRAFICOS.mkdir(parents=True, exist_ok=True)

    somas_por_municipio(df)
    medias_por_regiao(df)
    contagens_por_dependencia(df)

    print("\n[ok] Agrupamentos e gráficos prontos.")
    print("     Relatório e dashboard consomem estes arquivos.")


if __name__ == "__main__":
    main()