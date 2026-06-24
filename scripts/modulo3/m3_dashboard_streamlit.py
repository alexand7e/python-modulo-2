"""
MÓDULO 3 · DASHBOARD INTERATIVO — Streamlit
Análise de Dados — Módulo 3

Dashboard enxuto que consome o cruzamento pronto (não refaz o ETL).
Filtros por município/região/dependência/cargo; KPIs; gráficos e MAPA
interativo (lat/long) com Plotly.

    streamlit run scripts/modulo3/m3_dashboard_streamlit.py

Lê   : saida/modulo3/cruzamento.xlsx   (gerado por m3_cruzamento.py)

------------------------------------------------------------------------
PENSAMENTO COMPUTACIONAL AQUI:
  • Decomposição → cada KPI/gráfico/mapa é um bloco do dashboard.
  • Padrões      → "filtrar → agregar → desenhar" por widget.
  • Abstração    → st.dataframe / plotly abstraem a renderização.
  • Algoritmo    → carregar uma vez → widgets filtram na memória → mostrar.
------------------------------------------------------------------------
Rodar:
    1. ative o ambiente virtual
    2. streamlit run scripts/modulo3/m3_dashboard_streamlit.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent.parent
CRUZAMENTO = RAIZ / "saida" / "modulo3" / "cruzamento.xlsx"


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


def _kpi(label, valor, ajuda=None, cor="inverse"):
    delta = ajuda if ajuda is not None else None
    st.metric(label, valor, delta=delta, delta_color=cor)


def mapa_municipios(dff: pd.DataFrame) -> None:
    """Mapa interativo (Plotly) — um ponto por município, cor por população."""
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
        municipios,
        lat="Latitude", lon="Longitude",
        size="Matrículas", color="População",
        color_continuous_scale="YlGn",
        size_max=35, zoom=5.2,
        hover_name="Município",
        hover_data={"Região": True, "População": ":,", "Escolas": True,
                    "Matrículas": True, "Latitude": False, "Longitude": False},
        center={"lat": -5.8, "lon": -42.2},
        height=520,
    )
    fig.update_layout(map=dict(style="open-street-map"),
                      margin=dict(l=0, r=0, t=10, b=0),
                      coloraxis_colorbar=dict(title="População"))
    st.plotly_chart(fig, use_container_width=True)


def mapa_servidores(dff: pd.DataFrame) -> None:
    """Mapa de densidade de servidores (pontos) por município."""
    serv = (dff.dropna(subset=["Latitude", "Longitude",
                                "Remuneração"])
               .groupby(["Município", "Cargo"], as_index=False)
               .agg(Servidores=("CPF", "nunique"),
                    Remuneração_média=("Remuneração", "mean"),
                    Latitude=("Latitude", "first"),
                    Longitude=("Longitude", "first")))
    if serv.empty:
        st.info("Sem servidores com coordenadas no filtro atual.")
        return
    fig = px.scatter_map(
        serv,
        lat="Latitude", lon="Longitude",
        size="Servidores", color="Remuneração_média",
        color_continuous_scale="Viridis",
        size_max=30, zoom=5.2,
        hover_name="Município",
        hover_data={"Cargo": False, "Servidores": True,
                    "Remuneração_média": ":.2f",
                    "Latitude": False, "Longitude": False},
        center={"lat": -5.8, "lon": -42.2},
        height=480,
    )
    fig.update_layout(map=dict(style="carto-positron"),
                      margin=dict(l=0, r=0, t=10, b=0),
                      coloraxis_colorbar=dict(title="Remuneração média (R$)"))
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Dashboard · Dados Educacionais PI",
                       page_icon="📍", layout="wide")
    st.markdown(
        "<h1 style='margin-bottom:0'>📍 Dados Educacionais do Piauí</h1>",
        unsafe_allow_html=True,
    )
    st.caption("Módulo 3 — Análise de Dados · base cruzamento.xlsx "
               "· 3 bases cruzadas por Código IBGE")

    df = carregar()

    # ---------------- Filtros (sidebar) ----------------
    st.sidebar.markdown("### 🎛️ Filtros")
    st.sidebar.caption("Use os seletores abaixo para recortar a base.")

    regioes = ["Todas"] + sorted(df["Região"].dropna().unique())
    regiao = st.sidebar.selectbox("Região", regioes, index=0)

    muni_opcoes = sorted(df["Município"].dropna().unique())
    municipios = st.sidebar.multiselect("Municípios", muni_opcoes,
                                        default=muni_opcoes)

    dep_opcoes = sorted(df["Dependência"].dropna().unique())
    dependencias = st.sidebar.multiselect("Dependência",
                                            dep_opcoes, default=dep_opcoes)

    if "Cargo" in df.columns:
        cargo_opcoes = sorted(df["Cargo"].dropna().unique())
        cargos = st.sidebar.multiselect("Cargo", cargo_opcoes,
                                         default=cargo_opcoes)
    else:
        cargos = None

    if "Situação" in df.columns:
        sit_opcoes = sorted(df["Situação"].dropna().unique())
        situacoes = st.sidebar.multiselect("Situação do servidor",
                                            sit_opcoes, default=sit_opcoes)
    else:
        situacoes = None

    rem_min, rem_max = st.sidebar.slider(
        "Faixa de remuneração (R$)",
        float(df["Remuneração"].min() or 0),
        float(df["Remuneração"].max() or 0),
        (float(df["Remuneração"].min() or 0),
         float(df["Remuneração"].max() or 0)),
        step=100.0,
    )

    # aplica filtros
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

    if dff.empty:
        st.warning("Nenhum registro combina com o filtro atual. "
                   "Afrouxe algum seletor na barra lateral.")
        st.stop()

    # ---------------- KPIs ----------------
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Municípios", int(dff["Código_IBGE"].nunique()))
    c2.metric("Escolas", int(dff["CNPJ_Escola"].nunique()))
    c3.metric("Servidores", int(dff["CPF"].nunique()))
    c4.metric("Matrículas",
              f"{int(dff['Matrículas'].sum()):,}".replace(",", "."))
    c5.metric("Remuneração média",
              f"R$ {dff['Remuneração'].mean():,.2f}".replace(",", "X")
              .replace(".", ",").replace("X", "."))

    st.markdown("---")

    # ---------------- Mapa + ranking ----------------
    st.subheader("🗺️ Mapa de municípios (tamanho = matrículas, "
                  "cor = população)")
    mapa_municipios(dff)

    st.subheader("🏆 Ranking — matrículas por município")
    rank = (dff.groupby("Município")["Matrículas"].sum()
               .sort_values(ascending=True).reset_index())
    fig_rank = px.bar(rank, x="Matrículas", y="Município",
                      orientation="h", color="Matrículas",
                      color_continuous_scale="Greens",
                      height=max(300, 30 * len(rank)))
    fig_rank.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                            coloraxis_showscale=False)
    st.plotly_chart(fig_rank, use_container_width=True)

    # ---------------- Distribuições ----------------
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Servidores por dependência")
        dep = dff.groupby("Dependência")["CPF"].nunique().reset_index()
        fig_dep = px.bar(dep, x="Dependência", y="CPF", color="Dependência",
                         text="CPF", height=320)
        fig_dep.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_dep, use_container_width=True)

    with col2:
        st.markdown("#### Distribuição por região (remuneração média)")
        reg = dff.groupby("Região")["Remuneração"].mean().reset_index()
        fig_reg = px.bar(reg, x="Região", y="Remuneração", color="Região",
                         text_auto=".2f", height=320)
        fig_reg.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_reg, use_container_width=True)

    st.markdown("#### Pizza — escolas por situação")
    sit = dff.groupby("Situação")["CNPJ_Escola"].nunique().reset_index()
    fig_pie = px.pie(sit, values="CNPJ_Escola", names="Situação",
                      hole=0.4, height=360)
    fig_pie.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_pie, use_container_width=True)

    # ---------------- Mapa de servidores ----------------
    st.markdown("---")
    st.subheader("📍 Mapa de servidores (tamanho = nº, "
                  "cor = remuneração média)")
    mapa_servidores(dff)

    # ---------------- Tabela de detalhe ----------------
    st.subheader("👩‍🏫 Servidores (detalhe)")
    colunas = ["Município", "Nome_Escola", "Nome", "Cargo", "Situação",
               "Remuneração", "Admissão"]
    st.dataframe(dff[[c for c in colunas if c in dff.columns]].sort_values(
        "Município"), use_container_width=True)

    # ---------------- Download ----------------
    st.sidebar.markdown("---")
    st.sidebar.download_button(
        "⬇️ Baixar base filtrada (CSV)",
        dff.to_csv(index=False).encode("utf-8"),
        file_name="cruzamento_filtrado.csv",
        mime="text/csv",
    )

    # ---- >>> EXERCÍCIO DOS ALUNOS <<< ----
    # ------------------------------------------------------------------------
    # Adicione um filtro novo (ex.: por Situação da escola) e um mapa de
    # CALOR (hexbin) da remuneração por município. Plotly tem density_mapbox.
    #
    # Dica de prompt:
    #   "Em Plotly Express, gere um density_mapbox de latitude/longitude
    #    ponderado por Remuneração, com radius=30 e center no Piauí."
    # Implemente abaixo, recarregue com 'R' e confira no navegador.
    # ------------------------------------------------------------------------


if __name__ == "__main__":
    main()