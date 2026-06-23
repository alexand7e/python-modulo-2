"""
FRENTE 2 · VARIAÇÃO — PDF report individual
Módulo 2 — Automação de Documentos

O MESMO loop da Frente 1, trocando SÓ a saída: em vez de um .docx por
servidor, um .pdf por servidor. Repare como "ler + repetir" são idênticos
— muda apenas a peça "gerar saída" (slide 10).

    python3 scripts/frente2_pdf_reportlab.py

Lê   : saida/servidores_limpo.xlsx   (gerado pela Frente 0)
Grava: saida/pdfs/<nome>.pdf

------------------------------------------------------------------------
ESTE ARQUIVO É UM PONTO DE PARTIDA, NÃO O FIM.
Ele já gera um PDF simples e funcional. A PARTE BONITA (layout, cores,
brasão, rodapé...) está marcada como exercício. Use os 4 pilares:
  • o ESQUELETO (ler/repetir) já está pronto e você reaproveita;
  • o PADRÃO da Frente 1 se repete aqui;
  • a IA gera a VARIAÇÃO de layout — você avalia e ajusta.
------------------------------------------------------------------------
"""

import unicodedata
from pathlib import Path

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

RAIZ = Path(__file__).resolve().parent.parent
PLANILHA = RAIZ / "saida" / "servidores_limpo.xlsx"
PASTA_SAIDA = RAIZ / "saida" / "pdfs"


def nome_de_arquivo(nome: str) -> str:
    """'João Pedro Alves' -> 'joao_pedro_alves.pdf' (sem acento, sem espaço)."""
    sem_acento = (
        unicodedata.normalize("NFKD", nome)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return sem_acento.lower().replace(" ", "_") + ".pdf"


def gerar_um_pdf(linha: pd.Series) -> Path:
    """Gera UM PDF simples para UMA linha. (a peça que troca de biblioteca)

    Versão mínima e funcional: título + dados em linhas. Suficiente para
    PROVAR que o esqueleto funciona com reportlab. O capricho fica por
    conta do exercício lá embaixo.
    """
    destino = PASTA_SAIDA / nome_de_arquivo(linha["Nome"])
    c = canvas.Canvas(str(destino), pagesize=A4)
    largura, altura = A4

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, altura - 3 * cm, "FICHA DO SERVIDOR")

    # Dados, uma linha por campo
    c.setFont("Helvetica", 12)
    y = altura - 5 * cm
    campos = [
        ("Nome", linha["Nome"]),
        ("CPF", linha["CPF"]),
        ("Cargo", linha["Cargo"]),
        ("Lotação", linha["Lotacao"]),
        ("Admissão", linha["Data_Admissao"]),
        ("E-mail", linha["Email"]),
    ]
    for rotulo, valor in campos:
        c.drawString(2 * cm, y, f"{rotulo}: {valor}")
        y -= 0.9 * cm

    c.showPage()
    c.save()
    return destino


# ==========================================================================
# >>> EXERCÍCIOS DOS ALUNOS (escolha um ou mais; vá além do que foi dado) <<<
# --------------------------------------------------------------------------
# Tudo abaixo é "outra tarefa que você julgar necessária", pensada com os
# 4 pilares. Não há resposta única — o objetivo é DIRIGIR a IA e CONFERIR.
#
#  (a) LAYOUT INSTITUCIONAL: cabeçalho colorido, linha separadora, rodapé
#      com data de emissão e número de página. Prompt sugerido (slide 12):
#        "Adapte gerar_um_pdf para ter um cabeçalho com retângulo colorido,
#         título em branco, uma linha horizontal abaixo e um rodapé com a
#         data de hoje. Use reportlab."
#
#  (b) FILTRAR ANTES: gerar PDF só de uma secretaria (decomposição: filtrar
#      é um passo separado de gerar). Ex.: só "Secretaria de Saúde".
#
#  (c) UM PDF ÚNICO com TODOS os servidores (uma página por pessoa), em vez
#      de um arquivo por pessoa — repare que muda o ALGORITMO, não os dados.
#
#  (d) QR CODE ou número de protocolo no rodapé de cada ficha.
#
# Implemente no corpo de gerar_um_pdf (ou crie funções novas) e confira o
# resultado abrindo os PDFs em saida/pdfs/.
# ==========================================================================


def main() -> None:
    if not PLANILHA.exists():
        raise SystemExit(
            f"Não achei {PLANILHA.relative_to(RAIZ)}.\n"
            "Rode antes a Frente 0:  python3 scripts/frente0_ler_e_limpar.py"
        )

    df = pd.read_excel(PLANILHA, dtype=str)
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    # O MESMO loop da Frente 1 — só a função de saída mudou.
    total = 0
    for _, linha in df.iterrows():
        destino = gerar_um_pdf(linha)
        print(f"  [ok] {destino.name}")
        total += 1

    print(f"\n[ok] {total} PDFs gerados em: {PASTA_SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
