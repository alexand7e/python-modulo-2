#!/usr/bin/env python3
"""
main.py — Orquestrador do Módulo 3
====================================

Executa os 5 scripts do projeto em ordem, explica o que cada um faz,
mostra os resultados parciais e, ao final, exibe o resultado consolidado
(dashboard + arquivos gerados).

Uso:
    python3 main.py                     # executa tudo (modo automático)
    python3 main.py --explicar          # só explica, não executa
    python3 main.py --etapa 3           # pula direto para a etapa 3
    python3 main.py --dashboard         # abre só o Streamlit no fim

------------------------------------------------------------------------
Arquitetura do projeto (como os scripts se conectam):

    entrada/modulo3/  (3 bases "sujas")
          │
          ▼
    [0] notebook_etl.ipynb  ─── ETL: limpa as 3 bases  ──► saida/modulo3/*_limpo.xlsx
          │
          ├──► [1] m3_cruzamento.py   ─── merge por IBGE    ──► saida/modulo3/cruzamento.xlsx
          ├──► [2] m3_agrupamentos.py ─── groupby + gráficos ──► saida/modulo3/agrupamentos_*.xlsx + PNGs
          ├──► [3] m3_diff_versoes.py ─── diff v1 vs v2     ──► saida/modulo3/diff_v1_v2.xlsx
          ├──► [4] m3_relatorio_reportlab.py ─── PDF final  ──► saida/modulo3/relatorio.pdf
          └──► [5] m3_dashboard_streamlit.py  ─── dash interativo (abre no navegador)

    Fluxo dos dados neste script:
        1. Executa o notebook (ETL)          → 3 bases limpas
        2. Executa o cruzamento              → 1 base única (20 colunas)
        3. Executa os agrupamentos           → tabelas-síntese + 3 PNGs
        4. Compara versões (diff)            → mudanças detectadas
        5. Gera o relatório PDF              → 3 páginas com mapa
        6. Explica e sugere o dashboard      → streamlit run ...
------------------------------------------------------------------------
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SCRIPTS = RAIZ / "scripts" / "modulo3"
ENTRADA = RAIZ / "entrada" / "modulo3"
SAIDA = RAIZ / "saida" / "modulo3"
GRAFICOS = SAIDA / "graficos"

# ─── cores ───────────────────────────────────────────────────────────────
VERDE = "\033[92m"
AMARELO = "\033[93m"
AZUL = "\033[94m"
MAGENTA = "\033[95m"
NEGRITO = "\033[1m"
FIM = "\033[0m"


def titulo(texto: str, cor: str = AZUL) -> None:
    print(f"\n{cor}{NEGRITO}{'=' * 65}{FIM}")
    print(f"{cor}{NEGRITO}  {texto}{FIM}")
    print(f"{cor}{NEGRITO}{'=' * 65}{FIM}\n")


def ok(msg: str) -> None:
    print(f"  {VERDE}[OK]{FIM} {msg}")


def alerta(msg: str) -> None:
    print(f"  {AMARELO}[!]{FIM} {msg}")


def destaque(msg: str, cor=AZUL) -> None:
    print(f"  {cor}{NEGRITO}{msg}{FIM}")


def _check_venv():
    """Avisa se não estiver no ambiente virtual."""
    if not hasattr(sys, "real_prefix") and not (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        alerta("Parece que você NÃO está num ambiente virtual (.venv).")
        alerta("Crie e ative:  source .venv/bin/activate")


def _executar(script: str, descricao: str) -> bytes:
    """Roda um script Python e retorna a saída (stdout+stderr)."""
    caminho = SCRIPTS / script
    if not caminho.is_file():
        return f"  {AMARELO}[!] Arquivo não encontrado: {caminho}{FIM}".encode()
    print(f"  Rodando: python3 {script}")
    try:
        res = subprocess.run(
            [sys.executable, str(caminho)],
            capture_output=True, text=True, timeout=120, check=False,
        )
        if res.returncode != 0:
            alerta(f"  {script} retornou código {res.returncode}")
        return (res.stdout or "")[:3000] + (res.stderr or "")[:1000]
    except subprocess.TimeoutExpired:
        return f"  {AMARELO}[!] Timeout — {script} demorou demais (>120s){FIM}".encode()
    except Exception as e:
        return f"  {AMARELO}[!] Erro ao executar: {e}{FIM}".encode()


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 0 — Contexto do projeto
# ═══════════════════════════════════════════════════════════════════════════
def etapa0_contexto():
    titulo("Módulo 3 — Análise de Dados", MAGENTA)
    print("  Projeto com 2 módulos no mesmo repositório:")
    print(f"    {NEGRITO}Módulo 2{FIM} — Automação de Documentos (Word, PDF, Excel)")
    print(f"    {NEGRITO}Módulo 3{FIM} — Análise de Dados (merge, groupby, diff, gráficos, relatório PDF, dashboard)")
    print()
    print("  Neste main.py executamos APENAS o Módulo 3.")
    print()
    print("  Dados de entrada (3 bases fictícias 'sujas' — contexto Piauí):")
    for f in sorted(ENTRADA.iterdir()):
        if f.suffix == ".xlsx" and f.name != ".gitkeep":
            mb = f.stat().st_size / 1024
            print(f"    📄 {f.name:<35}  {mb:.1f} KB")
    print()

    _check_venv()
    print()


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 1 — ETL (notebook)
# ═══════════════════════════════════════════════════════════════════════════
def etapa1_notebook():
    titulo("Etapa 0 — notebook_etl.ipynb  (ETL)")
    print(textwrap.dedent("""\
    ── O que faz ──
      Lê as 3 bases "sujas" de entrada/modulo3/ e aplica limpezas:
        • Padroniza Código_IBGE (remove zeros/pontos)
        • Ajusta texto (espaços, caixa)
        • Converte números (população, matrículas, remuneração)
        • Normaliza datas (Admissão → dd/mm/aaaa)
        • Formata CPF (000.000.000-00)
        • Remove duplicatas (CPF)
        • Gera gráficos exploratórios (barras, pizza, linhas)
        • Exporta 3 planilhas LIMPAS + PNGs

    ── Conexão ──
      Gera saida/modulo3/*_limpo.xlsx — TUDO que vem depois depende disso.
      Sem o ETL, os demais scripts falham (eles verificam a existência).

    ── Saídas ──
      • saida/modulo3/municipios_limpo.xlsx      (12 municípios, 6 colunas)
      • saida/modulo3/escolas_limpo.xlsx          (37 escolas, 7 colunas)
      • saida/modulo3/servidores_limpo.xlsx       (24 servidores, 10 colunas)
      • saida/modulo3/graficos/barras_populacao.png
      • saida/modulo3/graficos/pizza_dependencia.png
      • saida/modulo3/graficos/linhas_matriculas.png
    """))

    # verifica se já rodou
    limpos = list(SAIDA.glob("*_limpo.xlsx"))
    if limpos:
        ok("Bases limpas já existem — notebook já foi executado:")
        for p in limpos:
            import pandas as pd
            df = pd.read_excel(p)
            print(f"       {p.name:<35}  {len(df):>4} linhas × {len(df.columns)} cols")
        print()
        return True
    else:
        alerta("Bases limpas NÃO encontradas. Executando notebook via nbconvert...")
        nb = SCRIPTS / "notebook_etl.ipynb"
        if not nb.is_file():
            alerta(f"{nb.name} não encontrado.")
            return False
        try:
            res = subprocess.run(
                ["jupyter", "nbconvert", "--execute", "--to", "notebook",
                 str(nb), "--output", "/tmp/_etl_m3.ipynb", "--stdout"],
                capture_output=True, text=True, timeout=180,
            )
            if res.returncode == 0:
                ok("Notebook executado com sucesso.")
                return True
            else:
                alerta(f"nbconvert falhou: {res.stderr[:500]}")
                return False
        except FileNotFoundError:
            alerta("jupyter nbconvert não encontrado. Execute o notebook manualmente:")
            print(f"  {NEGRITO}jupyter lab scripts/modulo3/notebook_etl.ipynb{FIM}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 2 — Cruzamento
# ═══════════════════════════════════════════════════════════════════════════
def etapa2_cruzamento():
    titulo("Etapa 1 — m3_cruzamento.py  (Merge)")
    print(textwrap.dedent("""\
    ── O que faz ──
      Junta as 3 bases limpas pela coluna Código_IBGE:
        1. Escolas + Municípios (inner join)  → cada escola ganha região/população/lat/lon
        2. Resultado + Servidores (left join) → cada servidor ganha dados do município e escola
      Depois confere chaves órfãs (municípios sem escola, servidores sem match).

    ── Conexão ──
      CONSOme municipios_limpo, escolas_limpo, servidores_limpo (ETL).
      PRODUz cruzamento.xlsx — a base única que alimenta agrupamentos,
       relatório e dashboard.

    ── Algoritmo ──
      merge(esc, mun, on='Código_IBGE', how='inner')  →  37 linhas
      merge(resultado, ser, on=['Código_IBGE','CNPJ_Escola'], how='left') → 45 linhas
    """))

    saida = SAIDA / "cruzamento.xlsx"
    if saida.is_file():
        import pandas as pd
        df = pd.read_excel(saida)
        ok(f"cruzamento.xlsx: {len(df)} linhas × {len(df.columns)} colunas")
        print()
        destaque("Colunas resultantes:")
        for c in df.columns:
            print(f"  • {c}")
        print()
        destaque("Amostra (5 primeiras linhas):")
        for _, row in df.head(5).iterrows():
            print(f"  {row.get('Município',''):<20} {row.get('Nome_Escola',''):<30} "
                  f"{row.get('Nome',''):<20} {row.get('Cargo',''):<20}")
        print()
        return True
    else:
        alerta("cruzamento.xlsx não encontrado. Executando m3_cruzamento.py...")
        saida_texto = _executar("m3_cruzamento.py", "Cruzamento de bases")
        print(saida_texto.decode() if isinstance(saida_texto, bytes) else saida_texto)
        return saida.is_file()


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 3 — Agrupamentos
# ═══════════════════════════════════════════════════════════════════════════
def etapa3_agrupamentos():
    titulo("Etapa 2 — m3_agrupamentos.py  (groupby + gráficos)")
    print(textwrap.dedent("""\
    ── O que faz ──
      A partir do cruzamento, calcula:
        • Soma de matrículas e remuneração POR MUNICÍPIO
        • Médias de remuneração e população POR REGIÃO
        • Contagem de escolas e servidores POR DEPENDÊNCIA (municipal/estadual/federal)
        + Exporta as 3 tabelas como .xlsx e 3 gráficos .png

    ── Conexão ──
      CONSOme cruzamento.xlsx (merge).
      PRODUz saida/modulo3/agrupamentos_*.xlsx + gráficos PNG.
      As tabelas-síntese e PNGs entram no relatório PDF e no dashboard.

    ── Algoritmo ──
      groupby('Município').agg(Matriculas='sum', Remuneracao='sum', Escolas='nunique')
      groupby('Região').agg(Remuneracao_media='mean', ...)
      groupby('Dependência').agg(Servidores='nunique', ...)
    """))

    # verifica resultados
    agrup = sorted(SAIDA.glob("agrupamentos_*.xlsx"))
    pngs = sorted(GRAFICOS.rglob("agrup_*.png"))
    if agrup:
        ok(f"{len(agrup)} tabela(s) de agrupamento gerada(s):")
        for p in agrup:
            import pandas as pd
            df = pd.read_excel(p)
            print(f"       {p.name:<40}  {len(df):>4} linhas × {len(df.columns)} cols")
    if pngs:
        ok(f"{len(pngs)} gráfico(s) gerado(s):")
        for p in pngs:
            print(f"       {p.relative_to(RAIZ)}")
    if not agrup and not pngs:
        alerta("Nenhum agrupamento encontrado. Executando...")
        saida_texto = _executar("m3_agrupamentos.py", "Agrupamentos e totais")
        print(saida_texto.decode() if isinstance(saida_texto, bytes) else saida_texto)
    print()


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 4 — Diff de versões
# ═══════════════════════════════════════════════════════════════════════════
def etapa4_diff():
    titulo("Etapa 3 — m3_diff_versoes.py  (Comparação de versões)")
    print(textwrap.dedent("""\
    ── O que faz ──
      Compara duas versões da mesma base (escolas_piaui_v1 vs v2) e classifica:
        • ADICIONADAS — CNPJ que existe em v2 mas não em v1
        • REMOVIDAS   — CNPJ que existia em v1 mas sumiu em v2
        • ALTERADAS   — mesmo CNPJ, mas algum campo mudou (ex.: matrícula, situação)
      Gera uma planilha com todas as mudanças + relatório no terminal.

    ── Conexão ──
      Este script é INDEPENDENTE: não consome o ETL nem o merge.
      Trabalha com arquivos de entrada (v1 e v2 na entrada/modulo3/).
      A saída (diff_v1_v2.xlsx) é citada pelo relatório PDF como audit trail.

    ── Algoritmo ──
      add  = chaves_v2 - chaves_v1
      rem  = chaves_v1 - chaves_v2
      alt  = v1.set_index(CNPJ) != v2.set_index(CNPJ)  (alinhado por chave)
    """))

    saida = SAIDA / "diff_v1_v2.xlsx"
    if saida.is_file():
        import pandas as pd
        df = pd.read_excel(saida)
        tipos = df["tipo_diff"].value_counts().to_dict()
        ok("Diff encontrado:")
        for tipo, qtd in tipos.items():
            print(f"       {tipo:<12} → {qtd} linha(s)")
        print()
        destaque("Detalhe das mudanças:")
        for _, row in df.iterrows():
            print(f"  {row['tipo_diff']:<10} "
                  f"{str(row.get('CNPJ_Escola','')):<18}  "
                  f"{str(row.get('Nome_Escola',''))}")
        print()
    else:
        alerta("diff_v1_v2.xlsx não encontrado. Executando...")
        saida_texto = _executar("m3_diff_versoes.py", "Diff de versões")
        print(saida_texto.decode() if isinstance(saida_texto, bytes) else saida_texto)
    print()


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 5 — Relatório PDF
# ═══════════════════════════════════════════════════════════════════════════
def etapa5_relatorio():
    titulo("Etapa 4 — m3_relatorio_reportlab.py  (Relatório PDF)")
    print(textwrap.dedent("""\
    ── O que faz ──
      Gera um relatório PDF institucional com:
        • Cabeçalho com título, fonte dos dados e data de extração
        • Seção de limitações conhecidas (vazios, duplicatas, chaves órfãs)
        • Tabela de síntese (municípios, escolas, servidores, regiões)
        • Gráficos embutidos (população, matrículas, servidores por região)
        • Tabela Top 5 municípios por matrícula
        • Comparação de versões (diff v1 vs v2)
        • 🗺️ MAPA dos municípios (scatter lat/lon, cor=população, tamanho=matrículas)
        • Rodapé com aviso de reprodução

    ── Conexão ──
      CONSOme:
        • cruzamento.xlsx            (do m3_cruzamento)
        • agrupamentos_*.xlsx        (do m3_agrupamentos)
        • diff_v1_v2.xlsx           (do m3_diff_versoes)
        • graficos/*.png             (do notebook e do m3_agrupamentos)
      PRODUz:
        • saida/modulo3/relatorio.pdf   (3 páginas, ~180 KB)
    """))

    saida = SAIDA / "relatorio.pdf"
    if saida.is_file():
        kb = saida.stat().st_size / 1024
        ok(f"relatorio.pdf: {kb:.0f} KB")
        destaque(f"📄 saida/modulo3/relatorio.pdf  ({kb:.0f} KB) — abra no seu leitor de PDF")
        # mostra as seções
        import subprocess as sp
        import re
        try:
            saida_txt = sp.run(
                ["python3", "-c",
                 "from PyPDF2 import PdfReader; r=PdfReader('saida/modulo3/relatorio.pdf'); "
                 "print(len(r.pages), 'páginas')" if False else ""],
                capture_output=True, text=True, timeout=5
            )
        except:  # noqa
            pass
        # fallback: usar strings do PDF
        try:
            content = saida.read_bytes()
            texts = []
            for match in re.finditer(rb"\((.*?)\)", content):
                t = match.group(1).decode("latin-1", errors="ignore")
                if 30 < len(t) < 100:
                    texts.append(t)
            destaque("Trechos do PDF detectados:")
            for t in texts[:10]:
                print(f"  • {t}")
        except:  # noqa
            pass
        print()
    else:
        alerta("relatorio.pdf não encontrado. Executando...")
        saida_texto = _executar("m3_relatorio_reportlab.py", "Relatório PDF")
        print(saida_texto.decode() if isinstance(saida_texto, bytes) else saida_texto)
    print()


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 6 — Dashboard (final)
# ═══════════════════════════════════════════════════════════════════════════
def etapa6_dashboard():
    titulo("Etapa 5 — m3_dashboard_streamlit.py  (Dashboard Interativo)", MAGENTA)
    print(textwrap.dedent("""\
    ── O que faz ──
      Dashboard web interativo que consome o cruzamento.xlsx e mostra:
        • 5 KPIs (Municípios, Escolas, Servidores, Matrículas, Remuneração média)
        • 🗺️ Mapa interativo (municípios — Plotly scatter_map: tamanho=matrículas, cor=população)
        • 🗺️ Mapa de servidores (densidade por município, cor=remuneração média)
        • Ranking de matrículas (gráfico de barras horizontal)
        • Barras: servidores por dependência, remuneração por região
        • Pizza: escolas por situação
        • Tabela de servidores detalhada
        • Filtros: região, municípios, dependência, cargo, situação, faixa de remuneração
        • Download da base filtrada (CSV)

    ── Conexão ──
      Lê:
        • saida/modulo3/cruzamento.xlsx   (produto final do merge)
      Tudo o que o dashboard exibe vem de UMA ÚNICA fonte.

    ── Como rodar ──
        streamlit run scripts/modulo3/m3_dashboard_streamlit.py
    """))

    # Verifica se cruzamento existe
    cruz = SAIDA / "cruzamento.xlsx"
    if cruz.is_file():
        import pandas as pd
        df = pd.read_excel(cruz)
        destaque("📊 Dados carregados pelo dashboard (cruzamento.xlsx):")
        print(f"  {len(df)} registros, {len(df.columns)} colunas")
        print(f"  {df['Código_IBGE'].nunique()} municípios")
        print(f"  {df['CNPJ_Escola'].nunique()} escolas")
        print(f"  {df['CPF'].nunique()} servidores")
        print(f"  {int(df['Matrículas'].sum()):,} matrículas no total".replace(",", "."))
        print(f"  R$ {df['Remuneração'].mean():.2f} remuneração média")
        print()
        destaque("🗺️ Captura do mapa (graficos/mapa_municipios_relatorio.png):")
        mapa_png = GRAFICOS / "mapa_municipios_relatorio.png"
        if mapa_png.is_file():
            print(f"  ✅ PNG do mapa gerado em: {mapa_png.relative_to(RAIZ)}")
        print()

    # Abre o dashboard
    script = SCRIPTS / "m3_dashboard_streamlit.py"
    if script.is_file():
        destaque("▶️ Iniciando Streamlit...")
        print("  Se o navegador não abrir automaticamente, acesse:")
        print(f"  {NEGRITO}http://localhost:8501{FIM}")
        print()
        # tenta abrir streamlit
        try:
            os.execvp("streamlit", [
                "streamlit", "run", str(script),
                "--", "--server.headless", "false",
            ])
        except FileNotFoundError:
            alerta("Streamlit não encontrado no PATH.")
            alerta("Instale com:  pip install streamlit")
            alerta("Depois rode:  streamlit run " + str(script))
        except OSError:
            pass
    else:
        alerta(f"Dashboard não encontrado: {script}")


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA FINAL — Resumo
# ═══════════════════════════════════════════════════════════════════════════
def etapa_resumo():
    titulo("Resumo final dos arquivos gerados", MAGENTA)
    print("  saida/modulo3/")
    for p in sorted(SAIDA.rglob("*")):
        if p.is_file() and p.name != ".gitkeep":
            rel = p.relative_to(RAIZ)
            kb = p.stat().st_size / 1024
            print(f"  📦 {str(rel):<50} {kb:>7.1f} KB")
    print()
    destaque("Pipeline completo:")
    print("  entrada/ → notebook_etl.ipynb (ETL) → *_limpo.xlsx")
    print("                                              ↓")
    print("                                     m3_cruzamento.py")
    print("                                              ↓")
    print("  ┌── m3_agrupamentos.py ←──── cruzamento.xlsx ────→ m3_dashboard_streamlit.py")
    print("  │         ↓                                        (dashboard interativo)")
    print("  │   agrupamentos_*.xlsx + PNGs")
    print("  │         ↓")
    print("  │   m3_relatorio_reportlab.py  ───→ relatorio.pdf  (com mapa)")
    print("  │")
    print("  └── m3_diff_versoes.py  ←── v1+v2  ───→ diff_v1_v2.xlsx")
    print()
    destaque("Comandos úteis para o dia a dia na aula:")
    print(f"  {NEGRITO}python3 main.py{FIM}                           "
          "— rodar tudo de novo")
    print(f"  {NEGRITO}streamlit run scripts/modulo3/m3_dashboard_streamlit.py{FIM}  "
          "— só o dashboard")
    print(f"  {NEGRITO}python3 scripts/modulo3/m3_cruzamento.py{FIM}           "
          "— só o cruzamento")
    print(f"  {NEGRITO}python3 scripts/modulo3/m3_relatorio_reportlab.py{FIM}  "
          "— só o relatório")
    print(f"  {NEGRITO}jupyter lab scripts/modulo3/notebook_etl.ipynb{FIM}     "
          "— abrir o notebook ETL")


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════
def main():
    args = set(sys.argv[1:])
    modo_explicar = "--explicar" in args or "--explicar" in args
    so_dashboard = "--dashboard" in args

    etapa0_contexto()

    if so_dashboard:
        etapa6_dashboard()
        return

    etapa1_notebook()
    etapa2_cruzamento()
    etapa3_agrupamentos()
    etapa4_diff()
    etapa5_relatorio()
    etapa_resumo()

    if "--dashboard" in args or "-d" in args:
        etapa6_dashboard()
    else:
        print(f"\n  {NEGRITO}Dica:{FIM} passe {NEGRITO}--dashboard{FIM} para abrir "
              f"o Streamlit ao final.")
        print(f"  Ou rode manualmente:")
        print(f"    {NEGRITO}streamlit run scripts/modulo3/m3_dashboard_streamlit.py{FIM}")


if __name__ == "__main__":
    main()
