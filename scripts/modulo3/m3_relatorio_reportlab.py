"""
MÓDULO 3 · RELATÓRIO PDF — boas práticas de relatório
Análise de Dados — Módulo 3

Gera um relatório em PDF com as BOAS PRÁTICAS que a aula pede:

    • Cabeçalho institucional (título, subtítulo)
    • Fonte dos dados (donos das três bases)
    • Data de extração (hoje, automática)
    • Limitações conhecidas (vazios, duplicatas removidas, chaves órfãs)
    • Tabelas, gráficos e MAPA (latitude/longitude) embutidos

    python3 scripts/modulo3/m3_relatorio_reportlab.py

Lê   : saida/modulo3/cruzamento.xlsx        (m3_cruzamento)
       saida/modulo3/agrupamentos_*.xlsx     (m3_agrupamentos)
       saida/modulo3/diff_v1_v2.xlsx        (m3_diff_versoes)
       saida/modulo3/graficos/*.png          (notebook + m3_agrupamentos)
Grava: saida/modulo3/relatorio.pdf

------------------------------------------------------------------------
PENSAMENTO COMPUTACIONAL AQUI:
  • Decomposição → cada seção do PDF é uma função (cabeçalho, corpo, anexos).
  • Padrões      → "escrever um PDF" repete o esqueleto da Frente 2 do Módulo 2.
  • Abstração    → "relatório de qualidade" abstrai um checklist de boas
                    práticas (fonte, data, limitações).
  • Algoritmo    → montar cabeçalho → tabela de sintese → gráficos → rodapé.
------------------------------------------------------------------------
"""

from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

RAIZ = Path(__file__).resolve().parent.parent.parent
SAIDA_DIR = RAIZ / "saida" / "modulo3"
GRAFICOS = SAIDA_DIR / "graficos"
CRUZAMENTO = SAIDA_DIR / "cruzamento.xlsx"
SAIDA = SAIDA_DIR / "relatorio.pdf"
MAPA_PNG = GRAFICOS / "mapa_municipios_relatorio.png"

FONTES = {
    "municipios": "IBGE — Cidades @dados.gov.br (planilha fictícia adaptada)",
    "escolas":    "INEP — Censo Escolar (planilha fictícia adaptada)",
    "servidores": "SEGEP-PI — Cadastro de servidores (planilha fictícia adaptada)",
}
LIMITACOES = [
    "Bases fictícias, geradas para fins didáticos (Módulo 3).",
    "Chave de cruzamento: Código IBGE; servidores associados por CNPJ da escola.",
    "Duplicatas de CPF foram removidas na limpeza (municipios_limpo / servidores_limpo).",
    "Latitude/Longitude podem conter imprecisões; normalização feita no notebook ETL.",
    "A comparação de versões (diff) considera CNPJ_Escola como chave única.",
]


# ==========================================================================
# ESTILOS
# ==========================================================================
def estilos():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Sub", parent=ss["Title"], fontSize=13,
                          alignment=TA_CENTER, textColor=colors.HexColor("#1B5E20")))
    ss.add(ParagraphStyle("Secao", parent=ss["Heading2"], fontSize=12,
                          textColor=colors.HexColor("#2E7D32"), spaceBefore=12))
    ss.add(ParagraphStyle("Meta", parent=ss["Normal"], fontSize=9,
                          alignment=TA_LEFT, textColor=colors.grey))
    return ss


def _coord_num(serie: pd.Series) -> pd.Series:
    """Normaliza Latitude/Longitude (texto com ',' ou '.') para float."""
    s = (serie.astype(str).str.strip().str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce")


def gerar_mapa_png(df: pd.DataFrame) -> Path:
    """Gera um PNG de mapa (scatter lat/lon) — um ponto por município,
    cor = população, tamanho = matrículas. Reaproveitado no relatório PDF."""
    base = (df.dropna(subset=["Latitude", "Longitude"])
              .groupby(["Município", "Região"], as_index=False)
              .agg(População=("População", "first"),
                   Matrículas=("Matrículas", "sum"),
                   Latitude=("Latitude", "first"),
                   Longitude=("Longitude", "first")))
    if base.empty:
        return None
    # garante numéricos
    base["População"] = pd.to_numeric(base["População"], errors="coerce")
    base["Matrículas"] = pd.to_numeric(base["Matrículas"], errors="coerce").fillna(0)
    base["Latitude"] = _coord_num(base["Latitude"])
    base["Longitude"] = _coord_num(base["Longitude"])
    base = base.dropna(subset=["Latitude", "Longitude"])

    fig, ax = plt.subplots(figsize=(10, 7))
    sc = ax.scatter(base["Longitude"], base["Latitude"],
                    s=base["Matrículas"] / 20 + 40,
                    c=base["População"], cmap="YlGn",
                    edgecolors="#1B5E20", linewidth=0.8, alpha=0.85)
    # anota o nome de cada município
    for _, r in base.iterrows():
        ax.annotate(r["Município"], (r["Longitude"], r["Latitude"]),
                    fontsize=7, ha="left", xytext=(4, 4),
                    textcoords="offset points")
    cbar = fig.colorbar(sc, ax=ax, shrink=0.7)
    cbar.set_label("População")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Mapa — Municípios do Piauí (tamanho = matrículas, "
                  "cor = população)", fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.4)
    fig.tight_layout()
    fig.savefig(MAPA_PNG, dpi=120)
    plt.close(fig)
    print(f"  [png]  {MAPA_PNG.relative_to(RAIZ)}  (mapa do relatório)")
    return MAPA_PNG


def cabecalho(ss):
    h = []
    h.append(Paragraph("RELATÓRIO DE ANÁLISE DE DADOS EDUCACIONAIS", ss["Title"]))
    h.append(Paragraph("Municípios, Escolas e Servidores do Piauí", ss["Sub"]))
    h.append(Spacer(1, 0.4 * cm))
    fonte_par = " | ".join(f"{k}: {v}" for k, v in FONTES.items())
    h.append(Paragraph(f"<b>Fonte dos dados:</b> {fonte_par}", ss["Meta"]))
    h.append(Paragraph(f"<b>Data de extração:</b> {date.today().strftime('%d/%m/%Y')}",
                       ss["Meta"]))
    h.append(Spacer(1, 0.4 * cm))
    return h


def secao_limitacoes(ss):
    corpo = [Paragraph("1 · Limitações conhecidas", ss["Secao"])]
    for lim in LIMITACOES:
        corpo.append(Paragraph(f"• {lim}", ss["Normal"]))
    corpo.append(Spacer(1, 0.4 * cm))
    return corpo


def secao_sintese(ss):
    """Tabela de síntese a partir do cruzamento."""
    corpo = [Paragraph("2 · Síntese do cruzamento", ss["Secao"])]
    df = pd.read_excel(CRUZAMENTO)
    linhas = [
        ["Municípios no cruzamento", str(df["Código_IBGE"].nunique())],
        ["Escolas (CNPJ únicos)",    str(df["CNPJ_Escola"].nunique())],
        ["Servidores (CPF únicos)",  str(df["CPF"].nunique())],
        ["Total de registros",       str(len(df))],
        ["Regiões distintas",        str(df["Região"].nunique())],
    ]
    t = Table(linhas, colWidths=[7 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F5E9")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
    ]))
    p = corpo.append
    p(t)
    p(Spacer(1, 0.4 * cm))
    return corpo


def secao_graficos(ss, arquivos, titulo):
    corpo = [Paragraph(titulo, ss["Secao"])]
    for nome, legenda in arquivos:
        p = GRAFICOS / (nome + ".png")
        if p.exists():
            corpo.append(Paragraph(legenda, ss["Normal"]))
            corpo.append(Image(str(p), width=12 * cm, height=7 * cm))
            corpo.append(Spacer(1, 0.3 * cm))
    return corpo


def secao_tabela_top_municipios(ss):
    corpo = [Paragraph("4 · Top 5 municípios por matrículas", ss["Secao"])]
    arq = SAIDA_DIR / "agrupamentos_soma_municipio.xlsx"
    if arq.exists():
        df = pd.read_excel(arq).head(5)
        dados = [["Município", "Matrículas", "Remuneração total", "Escolas"]]
        for _, r in df.iterrows():
            dados.append([
                str(r.get("Município", "")),
                str(int(r.get("Matriculas", 0))),
                f"R$ {r.get('Remuneracao', 0):.2f}",
                str(int(r.get("Escolas", 0))),
            ])
        t = Table(dados, colWidths=[4 * cm, 3 * cm, 4 * cm, 2.5 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]))
        corpo.append(t)
    corpo.append(Spacer(1, 0.5 * cm))
    return corpo


def secao_diff(ss):
    corpo = [Paragraph("5 · Mudanças entre versões das escolas (v1 vs v2)", ss["Secao"])]
    arq = SAIDA_DIR / "diff_v1_v2.xlsx"
    if arq.exists():
        df = pd.read_excel(arq)
        if "tipo_diff" in df.columns:
            cont = df["tipo_diff"].value_counts().to_dict()
            linha = " • ".join(f"{k}: {v}" for k, v in cont.items())
            corpo.append(Paragraph(f"<b>Resumo:</b> {linha}", ss["Normal"]))
        corpo.append(Spacer(1, 0.4 * cm))
    return corpo


def secao_mapa(ss, df_cruzamento: pd.DataFrame) -> list:
    """Seção 6 · Mapa de municípios (PNG gerado com matplotlib, lat/lon)."""
    corpo = [Paragraph("6 · Mapa — municípios do Piauí (lat/long)", ss["Secao"]),
             Paragraph(
                 "Cada ponto é um município. O <b>tamanho</b> da bolha mostra "
                 "as matrículas e a <b>cor</b> mostra a população. Mapas "
                 "geográficos enxutos como este são úteis em relatórios "
                 "impressos; versões interativas (com zoom e hover) ficam "
                 "no dashboard Streamlit.", ss["Normal"]),
             Spacer(1, 0.2 * cm)]
    png = gerar_mapa_png(df_cruzamento)
    if png is not None and png.exists():
        corpo.append(Image(str(png), width=15 * cm, height=10.5 * cm))
        corpo.append(Spacer(1, 0.4 * cm))
    else:
        corpo.append(Paragraph("(Sem coordenadas válidas para o mapa.)",
                               ss["Normal"]))
    return corpo


def rodape(ss):
    return [
        Spacer(1, 0.5 * cm),
        Paragraph(
            "Relatório gerado automaticamente — Módulo 3 · Análise de Dados. "
            "A reprodução deve citar a fonte. "
            "Verifique as limitações antes de qualquer decisão.",
            ParagraphStyle("Rodape", parent=ss["Normal"], fontSize=8,
                           textColor=colors.grey, alignment=TA_CENTER),
        ),
    ]


# ==========================================================================
# >>> EXERCÍCIO DOS ALUNOS — boas práticas que faltam <<<
# --------------------------------------------------------------------------
# O relatório já tem fonte, data e limitações. TÓPICOS QUE FALTAM e você pode
# adicionar (um por vez, depois CONFIRA no PDF):
#   (a) número de página no rodapé de cada página (use onPage do Platypus).
#   (b) logotipo/brasão no cabeçalho, alinhado à direita.
#   (c) sumário das DESIGUALDADES (ex.: gap remuneração entre municípios)
#       com um mini-gráfico inline.
#   (d) anexo: tabela completa de servidores (outras abas como anexos em PDF).
# Dica de prompt:
#   "Com reportlab Platypus, adicione número de página 'Página X' no rodapé
#    de cada página usando a função onFirstPage e onLaterPages do
#    SimpleDocTemplate."
# ==========================================================================


def main() -> None:
    if not CRUZAMENTO.exists():
        raise SystemExit(
            f"Não achei {CRUZAMENTO.relative_to(RAIZ)}.\n"
            "Rode antes:  python3 scripts/modulo3/m3_cruzamento.py"
        )
    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    ss = estilos()

    doc = SimpleDocTemplate(str(SAIDA), pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title="Relatório Módulo 3 — Dados Educacionais PI")
    elementos = []
    df_cruzamento = pd.read_excel(CRUZAMENTO)
    elementos += cabecalho(ss)
    elementos += secao_limitacoes(ss)
    elementos += secao_sintese(ss)
    elementos += secao_graficos(ss, [
        ("barras_populacao", "Gráfico 1 — Top 10 municípios por população"),
        ("agrup_barras_matriculas_municipio",
         "Gráfico 2 — Matrículas por município (top 10)"),
        ("agrup_pizza_regiao", "Gráfico 3 — Servidores por região"),
    ], "3 · Gráficos de síntese")
    elementos += secao_tabela_top_municipios(ss)
    elementos += secao_diff(ss)
    elementos += secao_mapa(ss, df_cruzamento)
    elementos += rodape(ss)

    doc.build(elementos)
    print(f"[ok] Relatório PDF salvo em: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()