"""
MÓDULO 3 · DASHBOARD INTERATIVO — Streamlit
Análise de Dados — Módulo 3

Dashboard profissional que consome o cruzamento pronto (não refaz o ETL).
Organizado em ABAS (Visão Geral, Mapas, Análises, Servidores, Sobre),
com a bandeira do Piauí no cabeçalho e identidade visual institucional.

    streamlit run scripts/modulo3/m3_dashboard_streamlit.py

Lê   : saida/modulo3/cruzamento.xlsx   (gerado por m3_cruzamento.py)
      modelo/assets/bandeira_piaui.png  (bandeira do estado)

------------------------------------------------------------------------
PENSAMENTO COMPUTACIONAL AQUI:
  • Decomposição → cada aba é um bloco isolado do dashboard.
  • Padrões      → "filtrar → agregar → desenhar" por widget.
  • Abstração    → st.tabs / plotly abstraem a renderização.
  • Algoritmo    → carregar uma vez → widgets filtram na memória → mostrar.
------------------------------------------------------------------------
Rodar:
    1. ative o ambiente virtual
    2. streamlit run scripts/modulo3/m3_dashboard_streamlit.py
"""

from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent.parent
CRUZAMENTO = RAIZ / "saida" / "modulo3" / "cruzamento.xlsx"
BANDEIRA = RAIZ / "modelo" / "assets" / "bandeira_piaui.png"

# ─── Cores oficiais do Piauí ─────────────────────────────────────────────
# Fonte: Manual de Identidade Visual do Governo do Estado do Piauí
COR_AZUL = "#0B1097"
COR_VERDE = "#56A134"
COR_AMARELO = "#FFD500"
COR_AZUL_ESCURO = "#08087A"
COR_CINZA = "#F0F2F6"


def _coord_num(serie: pd.Series) -> pd.Series:
    """Normaliza Latitude/Longitude (texto com ',' ou '.') para float."""
    s = (serie.astype(str).str.strip().str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce")


@st.cache_data(ttl=60)
def carregar() -> pd.DataFrame:
    if not CRUZAMENTO.exists():
        st.error(
            "Não achei saida/modulo3/cruzamento.xlsx.\n"
            "Rode antes:  python3 scripts/modulo3/m3_cruzamento.py"
        )
        st.stop()
    df = pd.read_excel(CRUZAMENTO)
    for col in ("População", "Matrículas"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Remuneração"] = pd.to_numeric(df.get("Remuneração"), errors="coerce")
    if "Latitude" in df.columns:
        df["Latitude"] = _coord_num(df["Latitude"])
    if "Longitude" in df.columns:
        df["Longitude"] = _coord_num(df["Longitude"])
    return df


def _fmt_brl(valor: float) -> str:
    """Formata um número como moeda brasileira: R$ 1.234,56"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ==========================================================================
# CSS — estilização profissional (injeção inline)
# ==========================================================================
def injetar_css() -> None:
    st.markdown(f"""
    <style>
    /* ── Cabeçalho com gradiente nas cores do Piauí ── */
    .piaui-header {{
        background: linear-gradient(135deg, {COR_AZUL} 0%, {COR_AZUL_ESCURO} 100%);
        padding: 1.5rem 2rem;
        border-radius: 0 0 12px 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin: -1rem -1rem 1.5rem -1rem;
    }}
    .piaui-header h1 {{
        color: white !important;
        font-size: 1.8rem !important;
        margin: 0 !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
    }}
    .piaui-header p {{
        color: {COR_AMARELO} !important;
        font-size: 0.9rem !important;
        margin-top: 0.3rem !important;
    }}
    .piaui-header .faixa {{
        height: 4px;
        background: linear-gradient(90deg,
            {COR_VERDE} 0%, {COR_VERDE} 33%,
            {COR_AMARELO} 33%, {COR_AMARELO} 66%,
            white 66%, white 100%);
        border-radius: 2px;
        margin-top: 0.8rem;
    }}

    /* ── Cards de KPI ── */
    div[data-testid="metric-container"] {{
        background: white;
        border: 1px solid #e0e0e0;
        border-left: 4px solid {COR_VERDE};
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        padding: 1rem 0.8rem;
    }}

    /* ── Abas ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        padding: 0.6rem 1.2rem;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
        font-size: 0.95rem;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COR_AZUL} !important;
        color: white !important;
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: {COR_CINZA};
    }}
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {{
        color: {COR_AZUL_ESCURO};
    }}

    /* ── Títulos de seção ── */
    h3 {{
        border-bottom: 3px solid {COR_AMARELO};
        padding-bottom: 0.3rem;
        color: {COR_AZUL_ESCURO};
    }}

    /* ── Rodapé ── */
    .piaui-footer {{
        text-align: center;
        color: #888;
        font-size: 0.8rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #e0e0e0;
    }}
    </style>
    """, unsafe_allow_html=True)


# ==========================================================================
# FUNÇÕES DE GRÁFICOS
# ==========================================================================
def mapa_municipios(dff: pd.DataFrame) -> None:
    """Mapa interativo — um ponto por município, cor por população."""
    municipios = (dff.dropna(subset=["Latitude", "Longitude"])
                     .groupby(["Município", "Região"], as_index=False)
                     .agg(População=("População", "first"),
                          Matrículas=("Matrículas", "sum"),
                          Escolas=("CNPJ_Escola", "nunique"),
                          Latitude=("Latitude", "first"),
                          Longitude=("Longitude", "first")))
    if municipios.empty:
        st.info("Sem coordenadas para desenhar o mapa com o filtro atual.")
        return
    fig = px.scatter_map(
        municipios, lat="Latitude", lon="Longitude",
        size="Matrículas", color="População",
        color_continuous_scale="YlGn", size_max=35, zoom=5.2,
        hover_name="Município",
        hover_data={"Região": True, "População": ":,", "Escolas": True,
                    "Matrículas": True, "Latitude": False, "Longitude": False},
        center={"lat": -5.8, "lon": -42.2}, height=550,
    )
    fig.update_layout(map=dict(style="open-street-map"),
                      margin=dict(l=0, r=0, t=10, b=0),
                      coloraxis_colorbar=dict(title="População"))
    st.plotly_chart(fig, use_container_width=True)


def mapa_servidores(dff: pd.DataFrame) -> None:
    """Mapa de densidade de servidores por município."""
    serv = (dff.dropna(subset=["Latitude", "Longitude", "Remuneração"])
                .groupby(["Município", "Cargo"], as_index=False)
                .agg(Servidores=("CPF", "nunique"),
                     Remuneração_média=("Remuneração", "mean"),
                     Latitude=("Latitude", "first"),
                     Longitude=("Longitude", "first")))
    if serv.empty:
        st.info("Sem servidores com coordenadas no filtro atual.")
        return
    fig = px.scatter_map(
        serv, lat="Latitude", lon="Longitude",
        size="Servidores", color="Remuneração_média",
        color_continuous_scale="Viridis", size_max=30, zoom=5.2,
        hover_name="Município",
        hover_data={"Cargo": False, "Servidores": True,
                    "Remuneração_média": ":.2f",
                    "Latitude": False, "Longitude": False},
        center={"lat": -5.8, "lon": -42.2}, height=500,
    )
    fig.update_layout(map=dict(style="carto-positron"),
                      margin=dict(l=0, r=0, t=10, b=0),
                      coloraxis_colorbar=dict(title="Remuneração média (R$)"))
    st.plotly_chart(fig, use_container_width=True)


# ==========================================================================
# ABA 1 — VISÃO GERAL
# ==========================================================================
def aba_visao_geral(dff: pd.DataFrame) -> None:
    st.markdown("### 📊 Indicadores principais")
    st.caption("Resumo dos dados filtrados — um cartão por indicador-chave.")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🏙️ Municípios", int(dff["Código_IBGE"].nunique()))
    c2.metric("🏫 Escolas", int(dff["CNPJ_Escola"].nunique()))
    c3.metric("👩‍🏫 Servidores", int(dff["CPF"].nunique()))
    c4.metric("🎒 Matrículas",
              f"{int(dff['Matrículas'].sum()):,}".replace(",", "."))
    c5.metric("💰 Remuneração média", _fmt_brl(dff["Remuneração"].mean()))

    st.markdown("---")
    st.markdown("### 📐 Distribuições")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Servidores por dependência administrativa")
        dep = dff.groupby("Dependência")["CPF"].nunique().reset_index()
        fig_dep = px.bar(dep, x="Dependência", y="CPF", color="Dependência",
                         text="CPF", height=340,
                         color_discrete_sequence=[COR_AZUL, COR_VERDE,
                                                  COR_AMARELO, "#888"])
        fig_dep.update_layout(showlegend=False,
                              margin=dict(l=0, r=0, t=0, b=0),
                              plot_bgcolor="white",
                              xaxis_title="", yaxis_title="Servidores")
        st.plotly_chart(fig_dep, use_container_width=True)

    with col2:
        st.markdown("#### Remuneração média por região")
        reg = dff.groupby("Região")["Remuneração"].mean().reset_index()
        fig_reg = px.bar(reg, x="Região", y="Remuneração", color="Região",
                         text_auto=".2f", height=340,
                         color_discrete_sequence=px.colors.qualitative.Set2)
        fig_reg.update_layout(showlegend=False,
                              margin=dict(l=0, r=0, t=0, b=0),
                              plot_bgcolor="white",
                              xaxis_title="", yaxis_title="R$")
        st.plotly_chart(fig_reg, use_container_width=True)

    st.markdown("#### 🥧 Escolas por situação")
    sit = dff.groupby("Situação")["CNPJ_Escola"].nunique().reset_index()
    fig_pie = px.pie(sit, values="CNPJ_Escola", names="Situação",
                     hole=0.4, height=380,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_pie.update_traces(textposition="inside", textinfo="label+percent")
    fig_pie.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                          showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)


# ==========================================================================
# ABA 2 — MAPAS
# ==========================================================================
def aba_mapas(dff: pd.DataFrame) -> None:
    st.markdown("### 🗺️ Mapa de municípios")
    st.caption("Cada bolha = um município · tamanho = matrículas · "
                "cor = população · clique para ver detalhes.")
    mapa_municipios(dff)

    st.markdown("---")
    st.markdown("### 📍 Mapa de servidores")
    st.caption("Cada bolha = um município · tamanho = nº de servidores · "
                "cor = remuneração média.")
    mapa_servidores(dff)


# ==========================================================================
# ABA 3 — ANÁLISES
# ==========================================================================
def aba_analises(dff: pd.DataFrame) -> None:
    st.markdown("### 🏆 Ranking — matrículas por município")
    rank = (dff.groupby("Município")["Matrículas"].sum()
               .sort_values(ascending=True).reset_index())
    fig_rank = px.bar(rank, x="Matrículas", y="Município",
                      orientation="h", color="Matrículas",
                      color_continuous_scale="Greens",
                      height=max(300, 32 * len(rank)))
    fig_rank.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                           coloraxis_showscale=False,
                           plot_bgcolor="white",
                           xaxis_title="Matrículas", yaxis_title="")
    fig_rank.update_traces(texttemplate="%{x}", textposition="outside")
    st.plotly_chart(fig_rank, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📊 Soma de remuneração por município")
    rem_muni = (dff.groupby("Município")["Remuneração"].sum()
                  .sort_values(ascending=True).reset_index())
    fig_rem = px.bar(rem_muni, x="Remuneração", y="Município",
                      orientation="h", color="Remuneração",
                      color_continuous_scale="Blues",
                      height=max(300, 32 * len(rem_muni)))
    fig_rem.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                          coloraxis_showscale=False,
                          plot_bgcolor="white",
                          xaxis_title="Remuneração total (R$)", yaxis_title="")
    st.plotly_chart(fig_rem, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔗 Relação: população × matrículas")
    if "População" in dff.columns:
        scatter = (dff.groupby(["Município", "Região"], as_index=False)
                      .agg(População=("População", "first"),
                           Matrículas=("Matrículas", "sum")))
        fig_sc = px.scatter(scatter, x="População", y="Matrículas",
                            color="Região", size="Matrículas",
                            hover_name="Município", height=400,
                            color_discrete_sequence=px.colors.qualitative.Set2)
        fig_sc.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                              plot_bgcolor="white")
        st.plotly_chart(fig_sc, use_container_width=True)


# ==========================================================================
# ABA 4 — SERVIDORES
# ==========================================================================
def aba_servidores(dff: pd.DataFrame) -> None:
    st.markdown("### 👩‍🏫 Servidores — detalhe")
    st.caption(f"{len(dff)} registros no filtro atual.")

    colunas = ["Município", "Nome_Escola", "Dependência", "Nome", "Cargo",
               "Situação", "Remuneração", "Admissão", "Email"]
    df_view = dff[[c for c in colunas if c in dff.columns]].copy()
    if "Remuneração" in df_view.columns:
        df_view["Remuneração"] = df_view["Remuneração"].apply(
            lambda v: _fmt_brl(v) if pd.notna(v) else "")
    df_view = df_view.sort_values(["Município", "Nome"])
    st.dataframe(df_view, use_container_width=True, height=500)

    st.markdown("---")
    st.markdown("### 💼 Distribuição por cargo")
    if "Cargo" in dff.columns:
        cargo = dff.groupby("Cargo")["CPF"].nunique().sort_values()
        fig_cargo = px.bar(cargo, orientation="h", color=cargo.values,
                           color_continuous_scale="Viridis",
                           height=max(300, 30 * len(cargo)))
        fig_cargo.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                                coloraxis_showscale=False,
                                plot_bgcolor="white",
                                xaxis_title="Servidores", yaxis_title="")
        st.plotly_chart(fig_cargo, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📅 Remuneração por data de admissão")
    if "Admissão" in dff.columns and "Remuneração" in dff.columns:
        df_adm = dff.dropna(subset=["Remuneração", "Admissão"]).copy()
        df_adm["Admissão_dt"] = pd.to_datetime(
            df_adm["Admissão"], errors="coerce", dayfirst=True)
        df_adm = df_adm.dropna(subset=["Admissão_dt"])
        if not df_adm.empty:
            fig_adm = px.scatter(df_adm, x="Admissão_dt", y="Remuneração",
                                  color="Cargo", hover_name="Nome",
                                  height=400,
                                  color_discrete_sequence=px.colors
                                  .qualitative.Set2)
            fig_adm.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                                   plot_bgcolor="white",
                                   xaxis_title="Admissão", yaxis_title="R$")
            st.plotly_chart(fig_adm, use_container_width=True)


# ==========================================================================
# ABA 5 — SOBRE
# ==========================================================================
def aba_sobre(df: pd.DataFrame) -> None:
    st.markdown("### ℹ️ Sobre este dashboard")
    st.markdown(f"""
    **Dashboard de Dados Educacionais do Piauí**  
    Módulo 3 — Análise de Dados

    ---

    **Bases de dados (fictícias, para fins didáticos):**
    - **Municípios** — 12 municípios com latitude, longitude, população e região
    - **Escolas** — 37 escolas com CNPJ, dependência e matrículas
    - **Servidores** — 24 servidores com cargo, remuneração e situação

    **Cruzamento:** as 3 bases foram unidas pela coluna `Código_IBGE`,
    produzindo `cruzamento.xlsx` com {len(df)} registros e
    {len(df.columns)} colunas.

    **Pipeline de geração:**
    ```
    entrada/modulo3/ (sujo)
        → notebook_etl.ipynb          (limpeza)
        → saida/modulo3/*_limpo.xlsx
        → m3_cruzamento.py            (merge por IBGE)
        → saida/modulo3/cruzamento.xlsx  ← este dashboard consome aqui
    ```

    **Boas práticas aplicadas:**
    - Fonte dos dados documentada
    - Limitações conhecidas (bases fictícias, chave por IBGE)
    - Comparação de versões (diff v1 vs v2) disponível em `diff_v1_v2.xlsx`
    - Relatório PDF institucional em `saida/modulo3/relatorio.pdf`

    **Atualizado em:** {date.today().strftime('%d/%m/%Y')}
    """)

    st.markdown("---")
    st.markdown(f"""
    <div class="piaui-footer">
        🇧🇷 Estado do Piauí · Módulo 3 — Análise de Dados · Curso de Python<br>
        Dashboard gerado com Streamlit + Plotly · Bandeira oficial do Piauí
    </div>
    """, unsafe_allow_html=True)


# ==========================================================================
# CABEÇALHO
# ==========================================================================
def cabecalho() -> None:
    """Renderiza o cabeçalho com bandeira do Piauí, título e faixa colorida."""
    bandeira_html = ""
    if BANDEIRA.exists():
        import base64
        with open(BANDEIRA, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        bandeira_html = (
            f'<img src="data:image/png;base64,{b64}" '
            f'style="height:60px;border-radius:4px;'
            f'box-shadow:0 2px 6px rgba(0,0,0,0.3);'
            f'border:2px solid white;vertical-align:middle;margin-right:1rem">'
        )
    st.markdown(f"""
    <div class="piaui-header">
        {bandeira_html}
        <span style="vertical-align:middle;display:inline-block">
            <h1>Dashboard · Dados Educacionais do Piauí</h1>
            <p>Módulo 3 — Análise de Dados · 3 bases cruzadas por Código IBGE</p>
        </span>
        <div class="faixa"></div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================================================
# FILTROS
# ==========================================================================
def aplicar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.markdown("### 🎛️ Filtros")
    st.sidebar.caption("Recorte a base por região, município e categoria.")

    regioes = ["Todas"] + sorted(df["Região"].dropna().unique())
    regiao = st.sidebar.selectbox("🗺️ Região", regioes, index=0)

    muni_opcoes = sorted(df["Município"].dropna().unique())
    municipios = st.sidebar.multiselect("🏙️ Municípios", muni_opcoes,
                                        default=muni_opcoes)

    dep_opcoes = sorted(df["Dependência"].dropna().unique())
    dependencias = st.sidebar.multiselect("🏫 Dependência", dep_opcoes,
                                            default=dep_opcoes)

    if "Cargo" in df.columns:
        cargo_opcoes = sorted(df["Cargo"].dropna().unique())
        cargos = st.sidebar.multiselect("💼 Cargo", cargo_opcoes,
                                         default=cargo_opcoes)
    else:
        cargos = None

    if "Situação" in df.columns:
        sit_opcoes = sorted(df["Situação"].dropna().unique())
        situacoes = st.sidebar.multiselect("📋 Situação do servidor",
                                            sit_opcoes, default=sit_opcoes)
    else:
        situacoes = None

    rem_min, rem_max = st.sidebar.slider(
        "💰 Faixa de remuneração (R$)",
        float(df["Remuneração"].min() or 0),
        float(df["Remuneração"].max() or 0),
        (float(df["Remuneração"].min() or 0),
         float(df["Remuneração"].max() or 0)),
        step=100.0,
    )

    dff = df.copy()
    if regiao != "Todas":
        dff = dff[dff["Região"] == regiao]
    dff = dff[dff["Município"].isin(municipios)]
    dff = dff[dff["Dependência"].isin(dependencias)]
    if cargos is not None:
        dff = dff[dff["Cargo"].isin(cargos)]
    if situacoes is not None:
        dff = dff[dff["Situação"].isin(situacoes)]
    dff = dff[dff["Remuneração"].between(rem_min, rem_max, inclusive="both")
               | dff["Remuneração"].isna()]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Registros filtrados:** {len(dff)}")

    st.sidebar.download_button(
        "⬇️ Baixar base filtrada (CSV)",
        dff.to_csv(index=False).encode("utf-8"),
        file_name="cruzamento_filtrado.csv",
        mime="text/csv",
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div style="text-align:center;font-size:0.75rem;color:#888">
    🇧🇷 Estado do Piauí · Módulo 3<br>Streamlit + Plotly
    </div>
    """, unsafe_allow_html=True)

    return dff


# ==========================================================================
# MAIN
# ==========================================================================
def main() -> None:
    st.set_page_config(page_title="Dashboard · Dados Educacionais PI",
                       page_icon="📊", layout="wide",
                       initial_sidebar_state="expanded")
    injetar_css()
    cabecalho()

    df = carregar()
    dff = aplicar_filtros(df)

    if dff.empty:
        st.warning("Nenhum registro combina com o filtro atual. "
                   "Afrouxe algum seletor na barra lateral.")
        st.stop()

    # ── Abas ──
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Visão Geral",
        "🗺️ Mapas",
        "📈 Análises",
        "👩‍🏫 Servidores",
        "ℹ️ Sobre",
    ])

    with tab1:
        aba_visao_geral(dff)
    with tab2:
        aba_mapas(dff)
    with tab3:
        aba_analises(dff)
    with tab4:
        aba_servidores(dff)
    with tab5:
        aba_sobre(df)

    # ---- >>> EXERCÍCIO DOS ALUNOS <<< ----
    # ------------------------------------------------------------------------
    # Adicione um novo filtro (ex.: por Situação da ESCOLA) e um mapa de
    # CALOR (density_mapbox) da remuneração por município.
    #
    # Dica de prompt:
    #   "Em Plotly Express, gere um density_mapbox de latitude/longitude
    #    ponderado por Remuneração, com radius=30 e center no Piauí.
    #    Coloque dentro de uma nova aba chamada 'Mapa de Calor'."
    # Implemente abaixo, recarregue com 'R' e confira no navegador.
    # ------------------------------------------------------------------------


if __name__ == "__main__":
    main()