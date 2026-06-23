"""
FRENTE 0 · PREPARAÇÃO — Ler e limpar a planilha
Módulo 2 — Automação de Documentos

O menor passo primeiro: abrir a planilha, OLHAR a sujeira e, um problema
por vez, limpar. No fim gravamos uma planilha LIMPA em
    saida/servidores_limpo.xlsx
que é o que as Frentes 1, 2 e 3 vão consumir.

    python3 scripts/frente0_ler_e_limpar.py

------------------------------------------------------------------------
PENSAMENTO COMPUTACIONAL AQUI (os 4 pilares da aula 1):
  • Decomposição → cada tipo de sujeira é uma função pequena e separada.
  • Padrões      → a sujeira se repete (datas, espaços, caixa do texto).
  • Abstração    → "limpar a planilha" = aplicar uma lista de limpezas.
  • Algoritmo    → ler → limpar campo por campo → conferir → salvar.
------------------------------------------------------------------------
Regra de ouro da aula: NUNCA mexer no original. Lemos de entrada/ e
gravamos em saida/. A planilha de entrada continua intocada.
"""

from pathlib import Path

import pandas as pd

# Caminhos relativos à raiz do projeto (este script vive em scripts/).
RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "entrada" / "servidores.xlsx"
SAIDA = RAIZ / "saida" / "servidores_limpo.xlsx"


# ==========================================================================
# 0) ABRIR E EXPLORAR  (Frente 0 · slide 7)
# ==========================================================================
def explorar(df: pd.DataFrame) -> None:
    """Mostra a planilha na tela. A sujeira aparece — e cria a necessidade de limpar."""
    print("=" * 60)
    print("PRIMEIRAS LINHAS (repare na sujeira):")
    print(df.head(8).to_string(index=False))
    print()
    print(f"Total de registros : {len(df)}")
    print(f"Colunas            : {list(df.columns)}")
    print("=" * 60)


# ==========================================================================
# 1) LIMPEZAS — uma função por problema (decomposição)
# ==========================================================================
def limpar_texto(df: pd.DataFrame) -> pd.DataFrame:
    """Espaços extras e caixa inconsistente → padronizar.

    'MARIA FERNANDA ROCHA', '  carlos eduardo lima ', 'LUCIANA  MENDES'
    viram todos 'Maria Fernanda Rocha', 'Carlos Eduardo Lima'...
    """
    colunas_texto = ["Nome", "Cargo", "Lotacao"]
    for col in colunas_texto:
        # .str.strip() tira espaços nas pontas;
        # .str.split() + join colapsa espaços duplos no meio.
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
            .str.split()
            .str.join(" ")
        )
    # O nome fica em Title Case (Primeira Letra De Cada Palavra Maiúscula).
    df["Nome"] = df["Nome"].str.title()
    return df


def limpar_cpf(df: pd.DataFrame) -> pd.DataFrame:
    """CPF em formatos mistos → um único padrão 000.000.000-00.

    '12345678909' e '123.456.789-09' devem virar a MESMA coisa, senão a
    busca por duplicatas não funciona.
    """
    def formatar(cpf: str) -> str:
        # Mantém só os dígitos.
        digitos = "".join(c for c in str(cpf) if c.isdigit())
        if len(digitos) != 11:
            # CPF com tamanho estranho: devolve como veio, marcando o problema.
            return f"INVÁLIDO({cpf})"
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"

    df["CPF"] = df["CPF"].map(formatar)
    return df


def limpar_datas(df: pd.DataFrame) -> pd.DataFrame:
    """Datas em vários formatos → dd/mm/aaaa.

    A coluna Data_Admissao vem caótica de propósito:
        2015-03-12, 05/07/2018, 12-11-2010, 2020/01/30, ...

    >>> EXERCÍCIO DOS ALUNOS <<<  (deixado em aberto de propósito)
    --------------------------------------------------------------------
    Pense no PADRÃO: todas essas strings representam uma data; muda só o
    separador e a ordem. O ALGORITMO é: interpretar a string como data e
    reescrever no formato dd/mm/aaaa.

    Dica de prompt para a IA (como ensina o slide 8):
        "Em pandas, converta a coluna Data_Admissao, que tem datas em
         formatos misturados (2015-03-12, 05/07/2018, 12-11-2010,
         2020/01/30), para o formato dd/mm/aaaa. Datas que não derem para
         interpretar devem virar um marcador, não quebrar o script."

    Apague o `return df` abaixo e implemente. Sugestão de caminho:
        pd.to_datetime(..., dayfirst=True, errors="coerce")
        e depois .dt.strftime("%d/%m/%Y")
    Depois, CONFIRA na planilha de saída — avaliar o resultado é parte
    do trabalho (slide 8).
    """
    # TODO(aluno): normalizar Data_Admissao para dd/mm/aaaa.
    return df


def remover_duplicatas(df: pd.DataFrame) -> pd.DataFrame:
    """Linha repetida (Ana Paula aparece 2x, mesmo CPF) → manter só a primeira.

    Rodamos DEPOIS de limpar o CPF, senão '12345678909' e '123.456.789-09'
    não seriam reconhecidos como a mesma pessoa (abstração: padronizar
    antes de comparar).
    """
    antes = len(df)
    df = df.drop_duplicates(subset="CPF", keep="first").reset_index(drop=True)
    removidas = antes - len(df)
    if removidas:
        print(f"  [info] {removidas} duplicata(s) removida(s) por CPF.")
    return df


def preencher_vazios(df: pd.DataFrame) -> pd.DataFrame:
    """Campos vazios → preencher com um marcador legível, nunca deixar 'NaN'."""
    df["Email"] = df["Email"].fillna("").replace("", "(e-mail não informado)")
    df["Lotacao"] = df["Lotacao"].fillna("").replace("", "(lotação não informada)")
    return df


# ==========================================================================
# 2) ALGORITMO PRINCIPAL — a ordem importa
# ==========================================================================
def main() -> None:
    if not ENTRADA.exists():
        raise SystemExit(
            f"Não achei a planilha em {ENTRADA}.\n"
            "Rode antes:  python3 iniciando_a_aula.py"
        )

    # --- LER ---
    df = pd.read_excel(ENTRADA, dtype=str)  # dtype=str: deixa tudo como texto por enquanto
    print("\n>>> ANTES da limpeza:")
    explorar(df)

    # --- LIMPAR (cada passo é uma função; a ordem é o algoritmo) ---
    df = limpar_texto(df)
    df = limpar_cpf(df)
    df = limpar_datas(df)          # <- exercício dos alunos
    df = remover_duplicatas(df)    # depende do CPF já padronizado
    df = preencher_vazios(df)

    print("\n>>> DEPOIS da limpeza:")
    explorar(df)

    # --- SALVAR (em saida/, nunca por cima do original) ---
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(SAIDA, index=False)
    print(f"\n[ok] Planilha limpa salva em: {SAIDA.relative_to(RAIZ)}")
    print("     É ESTE arquivo que as Frentes 1, 2 e 3 vão usar.")


if __name__ == "__main__":
    main()
