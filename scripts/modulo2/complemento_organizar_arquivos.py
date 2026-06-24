"""
COMPLEMENTO — Gerenciar arquivos em lote
Módulo 2 — Automação de Documentos

Até agora o "item" do nosso loop era uma LINHA da planilha. Agora o item
é um ARQUIVO. Mesma lógica (ler → para cada → agir), novo alvo (slide 15).

    python3 scripts/complemento_organizar_arquivos.py            # só MOSTRA (seguro)
    python3 scripts/complemento_organizar_arquivos.py --aplicar  # de fato renomeia

==========================================================================
REGRA DE OURO (slide 15): TESTE SEM APLICAR PRIMEIRO.
Imprima o nome novo ANTES de renomear. Em lote, o erro é irreversível.
Por isso, sem --aplicar, este script só MOSTRA o que faria.
==========================================================================
"""

import argparse
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
PASTA_OFICIOS = RAIZ / "saida" / "modulo2" / "oficios"

ANO = 2026


def planejar_renomeacao(pasta: Path) -> list[tuple[Path, str]]:
    """Lê os ofícios e PLANEJA o novo nome, sem tocar em nada.

    Padroniza, por exemplo:
        oficio_03_maria_fernanda_rocha.docx
        ->  2026_oficio_003_maria_fernanda_rocha.docx
    (número com 3 dígitos e prefixo do ano — bom para ordenar e arquivar.)

    Retorna uma lista de pares (arquivo_atual, nome_novo). Quem decide se
    aplica é o main — aqui só pensamos. (separar PLANEJAR de APLICAR é
    abstração: o mesmo plano serve para conferir e para executar.)
    """
    plano: list[tuple[Path, str]] = []
    for arquivo in sorted(pasta.glob("oficio_*.docx")):
        # Captura número e "resto" do nome com uma expressão regular.
        m = re.match(r"oficio_(\d+)_(.+)\.docx", arquivo.name)
        if not m:
            continue
        numero, resto = m.group(1), m.group(2)
        nome_novo = f"{ANO}_oficio_{int(numero):03d}_{resto}.docx"
        plano.append((arquivo, nome_novo))
    return plano


def main() -> None:
    parser = argparse.ArgumentParser(description="Renomear ofícios em lote (com segurança).")
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="Sem esta flag, o script só MOSTRA o que faria (modo seguro).",
    )
    args = parser.parse_args()

    if not PASTA_OFICIOS.exists():
        raise SystemExit(
            f"Não achei {PASTA_OFICIOS.relative_to(RAIZ)}.\n"
            "Rode antes a Frente 1:  python3 scripts/frente1_oficios_word.py"
        )

    plano = planejar_renomeacao(PASTA_OFICIOS)
    if not plano:
        raise SystemExit("Nenhum ofício para renomear (a pasta está vazia?).")

    modo = "APLICANDO" if args.aplicar else "SIMULAÇÃO (nada será alterado)"
    print(f"=== Renomear em lote — {modo} ===\n")

    for atual, nome_novo in plano:
        print(f"  {atual.name}")
        print(f"    -> {nome_novo}")
        if args.aplicar:
            atual.rename(atual.with_name(nome_novo))

    print(f"\nTotal: {len(plano)} arquivo(s).")
    if not args.aplicar:
        print("\nGostou do resultado acima? Rode de novo com  --aplicar  para valer.")
    else:
        print("\n[ok] Arquivos renomeados.")


# ==========================================================================
# >>> EXERCÍCIO PRINCIPAL DOS ALUNOS: ORGANIZAR POR SECRETARIA <<<
# --------------------------------------------------------------------------
# Slide 15: "Mover cada ofício para a subpasta da sua secretaria, cruzando
# com a lotação da planilha."   ->   saida/modulo2/oficios/Secretaria_de_Educacao/...
#
# Pense com os 4 pilares:
#   • DECOMPOSIÇÃO: (1) ler a planilha p/ saber a lotação de cada número de
#       ofício; (2) para cada arquivo, descobrir a secretaria; (3) criar a
#       subpasta; (4) mover.
#   • PADRÃO: todo arquivo segue o mesmo destino = pasta da sua secretaria.
#   • ABSTRAÇÃO: "organizar" = mapear arquivo -> pasta-destino, depois mover.
#   • ALGORITMO: planejar TODOS os movimentos, MOSTRAR, e só então mover
#       (a mesma Regra de Ouro: simular antes de aplicar).
#
# Esqueleto para você completar (apague o `pass` e implemente):
def organizar_por_secretaria(pasta: Path, aplicar: bool = False) -> None:
    """Mover cada ofício para uma subpasta com o nome da sua secretaria."""
    # DICA: leia saida/modulo2/servidores_limpo.xlsx com pandas para mapear
    #   Numero_Oficio -> Lotacao, e use shutil.move para mover.
    # Lembre-se de criar a subpasta com .mkdir(parents=True, exist_ok=True)
    # e de NUNCA mover de verdade sem antes mostrar o plano.
    pass
# ==========================================================================


if __name__ == "__main__":
    main()
