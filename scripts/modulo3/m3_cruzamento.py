"""
MÓDULO 3 · CRUZAMENTO DE BASES — merge por Código IBGE
Análise de Dados — Módulo 3

Juntamos as TRÊS bases (municípios, escolas, servidores) pela coluna em
comum `Código_IBGE`. É o mesmo esqueleto da aula, com a peça "gerar saída"
troca por "fazer um merge":

    ler as três limpas  →  merge por IBGE  →  conferir perdas  →  salvar.

    python3 scripts/modulo3/m3_cruzamento.py

Lê   : saida/modulo3/municipios_limpo.xlsx
       saida/modulo3/escolas_limpo.xlsx
       saida/modulo3/servidores_limpo.xlsx   (gerados pelo notebook_etl.ipynb)
Grava: saida/modulo3/cruzamento.xlsx

------------------------------------------------------------------------
PENSAMENTO COMPUTACIONAL AQUI:
  • Decomposição → cada merge é um passo isolado e conferido.
  • Padrões      → a chave (Código_IBGE) se repete nas três tabelas.
  • Abstração    → "cruzar" = juntar por chave comum (merge).
  • Algoritmo    → juntar municípios↔escolas, depois o resultado↔servidores,
                   e a cada passo CONFERIR quantas linhas sobraram.
------------------------------------------------------------------------
Regra de ouro: NUNCA mexer no original. Lemos de saida/modulo3/*_limpo.xlsx
grimado pelo notebook ETL, e gravamos em saida/modulo3/cruzamento.xlsx.
"""

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent.parent
ENTRADA = RAIZ / "saida" / "modulo3"
SAIDA = RAIZ / "saida" / "modulo3" / "cruzamento.xlsx"


def carregar_bases() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Lê as três bases já limpas pelo notebook ETL."""
    df_mun = pd.read_excel(ENTRADA / "municipios_limpo.xlsx")
    df_esc = pd.read_excel(ENTRADA / "escolas_limpo.xlsx")
    df_ser = pd.read_excel(ENTRADA / "servidores_limpo.xlsx")
    # padronizar tipos da chave, por garantia
    for df in (df_mun, df_esc, df_ser):
        df["Código_IBGE"] = pd.to_numeric(df["Código_IBGE"], errors="coerce").astype("Int64")
    return df_mun, df_esc, df_ser


# ==========================================================================
# 1) MERGE — um por vez, conferindo a cada par
# ==========================================================================
def cruzar(
    df_mun: pd.DataFrame, df_esc: pd.DataFrame, df_ser: pd.DataFrame
) -> pd.DataFrame:
    """Junta escolas→municípios (inner) e depois servidores→resultado (left).

    >>> EXERCÍCIO DOS ALUNOS  <<<
    --------------------------------------------------------------------
    Escolher o TIPO de join é parte do problema. Aqui usamos:

      • inner  municípios↔escolas    : só municípios que têm escola (e vice-versa)
      • left   ↔servidores           : cada servidor fica, mesmo se a escola sumiu

    Sua tarefa: PENSE no que acontece se trocar o primeiro para `left`.
    Quantas linhas a mais? E se for `outer`? Teste, CONFIRA (slide 8) e
    decida o que faz mais sentido para o relatório final.

    Dica de prompt para a IA:
        "Em pandas, faça um merge de df_esc (escolas) com df_mun (municípios)
         pela coluna Código_IBGE usando how='left' e mostre quais municípios
         ficaram sem escola."
    """
    # Passo 1: escolas + municípios
    base = df_esc.merge(
        df_mun[["Código_IBGE", "Município", "Latitude", "Longitude",
                 "População", "Região"]],
        on="Código_IBGE",
        how="inner",
        suffixes=("", "_mun"),
    )
    print(f"  [passo 1] escolas+municípios (inner): {len(base)} linhas")

    # Passo 2: + servidores (left, para não perder ninguém)
    final = base.merge(
        df_ser,
        on=["Código_IBGE", "CNPJ_Escola"],
        how="left",
        suffixes=("", "_ser"),
    )
    print(f"  [passo 2] +servidores (left)       : {len(final)} linhas")
    print(f"           colunas resultantes: {len(final.columns)}")
    return final


# ==========================================================================
# 2) CONFERIR — chaves órfãs (abstração: "o que sobrou de cada lado?")
# ==========================================================================
def conferir_chaves(df_mun, df_esc, df_ser, df_final) -> None:
    """Mostra quantos IBGEs/servidores ficaram de fora — parte do trabalho."""
    ibge_mun = set(df_mun["Código_IBGE"].dropna())
    ibge_esc = set(df_esc["Código_IBGE"].dropna())
    ibge_final = set(df_final["Código_IBGE"].dropna())

    mun_sem_escola = sorted(ibge_mun - ibge_esc)
    esc_sem_mun = sorted(ibge_esc - ibge_mun)
    print("\n--- Conferência de chaves ---")
    print(f"  Municípios sem escola : {len(mun_sem_escola)}  {mun_sem_escola[:5]}")
    print(f"  Escolas sem município : {len(esc_sem_mun)}  {esc_sem_mun[:5]}")
    print(f"  IBGE no resultado     : {len(ibge_final)}")
    n_serv = df_ser.loc[~df_ser["Código_IBGE"].isin(ibge_final), "CPF"].count()
    print(f"  Servidores órfãos (sem match no cruzamento): {n_serv}")


# ==========================================================================
# 3) ALGORITMO PRINCIPAL
# ==========================================================================
def main() -> None:
    if not (ENTRADA / "municipios_limpo.xlsx").exists():
        raise SystemExit(
            "Faltam as bases limpas. Rode antes o notebook:\n"
            "  jupyter lab scripts/modulo3/notebook_etl.ipynb"
        )

    df_mun, df_esc, df_ser = carregar_bases()
    print(f"carregado: municípios={len(df_mun)}, escolas={len(df_esc)}, "
          f"servidores={len(df_ser)}")

    df_final = cruzar(df_mun, df_esc, df_ser)
    conferir_chaves(df_mun, df_esc, df_ser, df_final)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_excel(SAIDA, index=False)
    print(f"\n[ok] Cruzamento salvo em: {SAIDA.relative_to(RAIZ)}")
    print("     É ESTE arquivo que m3_agrupamentos, m3_relatorio e o dashboard vão usar.")


if __name__ == "__main__":
    main()