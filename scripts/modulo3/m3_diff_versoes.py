"""
MÓDULO 3 · COMPARAÇÃO DE DUAS VERSÕES DE UMA MESMA BASE — diff
Análise de Dados — Módulo 3

Receba duas versões da mesma planilha (um "antes" e um "depois") e detecte
AUTOMATICAMENTE o que aconteceu entre elas:

    linhas ADICIONADAS  →  existem em v2, mas não em v1
    linhas REMOVIDAS    →  existem em v1, mas não em v2
    linhas ALTERADAS    →  mesma chave, mas algum campo mudou

    python3 scripts/modulo3/m3_diff_versoes.py

Lê   : entrada/modulo3/escolas_piaui_v1.xlsx
       entrada/modulo3/escolas_piaui_v2.xlsx
Grava: saida/modulo3/diff_v1_v2.xlsx   (+ relatório no terminal)

------------------------------------------------------------------------
PENSAMENTO COMPUTACIONAL AQUI:
  • Decomposição → "o que mudou?" vira 3 perguntas: +linhas, -linhas, ~linhas.
  • Padrões      → comparar pela CHAVE (CNPJ_Escola) e olhar os demais campos.
  • Abstração    → "diff de versão" = separar por chave e comparar valores.
  • Algoritmo    → alinhar por chave → checar exclusão/inclusão/alteração →
                    relatar.
------------------------------------------------------------------------
Boa prática de auditoria: este mesmo padrão serve p/ qualquer base que você
receba em duas versões (CRUD, snapshots mensais, polos antigo x novo…).
"""

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent.parent
ENTRADA = RAIZ / "entrada" / "modulo3"
V1 = ENTRADA / "escolas_piaui_v1.xlsx"
V2 = ENTRADA / "escolas_piaui_v2.xlsx"
SAIDA = RAIZ / "saida" / "modulo3" / "diff_v1_v2.xlsx"

# A chave que identifica cada linha de forma única. Aqui é o CNPJ da escola.
CHAVE = "CNPJ_Escola"


def carregar() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not V1.exists() or not V2.exists():
        raise SystemExit(
            "Faltam escolas_piaui_v1.xlsx ou escolas_piaui_v2.xlsx em "
            f"{ENTRADA.relative_to(RAIZ)}"
        )
    v1 = pd.read_excel(V1, dtype=str)
    v2 = pd.read_excel(V2, dtype=str)
    # normaliza a chave como texto limpo p/ comparar
    for df in (v1, v2):
        df[CHAVE] = df[CHAVE].astype(str).str.strip()
    # padroniza uma coluna numérica importante como texto p/ comparar
    for df in (v1, v2):
        if "Matrículas" in df.columns:
            df["Matrículas"] = df["Matrículas"].astype(str).str.strip()
    return v1, v2


# ==========================================================================
# 1) ADICIONADAS / REMOVIDAS — operação de conjuntos pela chave
# ==========================================================================
def adicoes_remocoes(v1: pd.DataFrame, v2: pd.DataFrame):
    chaves_v1 = set(v1[CHAVE])
    chaves_v2 = set(v2[CHAVE])

    adicionadas = chaves_v2 - chaves_v1
    removidas = chaves_v1 - chaves_v2

    linhas_add = v2[v2[CHAVE].isin(adicionadas)].copy()
    linhas_add["tipo_diff"] = "ADICIONADA"
    linhas_rem = v1[v1[CHAVE].isin(removidas)].copy()
    linhas_rem["tipo_diff"] = "REMOVIDA"

    print(f"  [+] linhas adicionadas : {len(linhas_add)}")
    print(f"  [-] linhas removidas  : {len(linhas_rem)}")
    if len(linhas_add):
        print("      adicionadas:")
        for _, r in linhas_add.iterrows():
            print(f"        {r[CHAVE]:<18} {r.get('Nome_Escola','')}")
    if len(linhas_rem):
        print("      removidas:")
        for _, r in linhas_rem.iterrows():
            print(f"        {r[CHAVE]:<18} {r.get('Nome_Escola','')}")
    return linhas_add, linhas_rem


# ==========================================================================
# 2) ALTERADAS — mesma chave, algum campo diferente
# ==========================================================================
def alteradas(v1: pd.DataFrame, v2: pd.DataFrame) -> pd.DataFrame:
    """Mesma chave, mas ao menos um campo mudou de valor."""
    comum = v1[CHAVE].isin(v2[CHAVE])
    v1_com = v1[comum].set_index(CHAVE)
    v2_com = (v2[v2[CHAVE].isin(set(v1[CHAVE]))]).set_index(CHAVE)
    # mantém só as colunas em comum
    cols = [c for c in v1_com.columns if c in v2_com.columns]
    v1_com = v1_com[cols]
    v2_com = v2_com[cols]

    # reindex para alinhar pela chave
    idx = v1_com.index.intersection(v2_com.index)
    a = v1_com.loc[idx]
    b = v2_com.loc[idx]

    diferente = (a.astype(str) != b.astype(str))
    # só chaves em que ao menos uma coluna é diferente
    mascara_linha = diferente.any(axis=1)

    alterados = b[mascara_linha].copy()
    alterados = alterados.reset_index()  # traz CHAVE de volta como coluna
    alterados.insert(0, "tipo_diff", "ALTERADA")

    print(f"  [~] linhas alteradas  : {len(alterados)}")
    # detalha quais colunas mudaram
    for _, row_alt in alterados.iterrows():
        chv = str(row_alt.get(CHAVE, "?"))
        mudancas = [c for c in cols
                    if str(a.loc[chv, c]) != str(b.loc[chv, c])]
        if mudancas:
            trecho = ", ".join(f"{c}: '{a.loc[chv,c]}'→'{b.loc[chv,c]}'"
                               for c in mudancas)
            print(f"      {chv:<18} {mudancas}")
    return alterados


# ==========================================================================
# 3) >>> EXERCÍCIO DOS ALUNOS — marcar QUAL coluna mudou, não só a linha <<<
# --------------------------------------------------------------------------
# Hoje nós listamos as colunas que mudaram no terminal, mas a planilha de
# saída não as destaca por campo. Sua tarefa: enriquecer `diff_v1_v2.xlsx`
# com uma coluna `campos_alterados` (lista de colunas mudadas) ao lado de
# cada linha ALTERADA.
#
# Dica de prompt:
#   "Para cada linha alterada em um DataFrame, adicione uma coluna
#    'campos_alterados' contendo a lista (em texto) das colunas cujo valor
#    difere entre v1 e v2, já alinhados pela coluna CNPJ_Escola."
# Implemente e confira abrindo o .xlsx de saída.
# ==========================================================================


def main() -> None:
    v1, v2 = carregar()
    print(f"v1: {len(v1)} linhas | v2: {len(v2)} linhas | chave: {CHAVE}")
    print("-" * 60)

    add, rem = adicoes_remocoes(v1, v2)
    alt = alteradas(v1, v2)

    # reúne tudo numa só planilha de relatório
    resumo = pd.concat([add, rem, alt], ignore_index=True, sort=False)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    resumo.to_excel(SAIDA, index=False)
    print("\n" + "=" * 60)
    print(f"[ok] diff salvo em: {SAIDA.relative_to(RAIZ)}")
    print("     agora o relatório (m3_relatorio) pode citar as mudanças.")


if __name__ == "__main__":
    main()