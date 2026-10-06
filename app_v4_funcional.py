import streamlit as st
import pandas as pd
import plotly.express as px
from unidecode import unidecode

# ======================================================
# CONFIG
# ======================================================

st.set_page_config(
    page_title="SPI Executive Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 SPI Executive Dashboard")

# ======================================================
# FUNÇÕES
# ======================================================

def detectar_coluna(df, texto):
    for col in df.columns:
        if texto.lower() in str(col).lower():
            return col
    return None


def normalizar(valor):

    if pd.isna(valor):
        return ""

    return (
        unidecode(str(valor))
        .upper()
        .strip()
    )


def classificar_spi(valor):

    if pd.isna(valor):
        return "⚪ Sem Dados"

    if valor > 5:
        return "🟢 Crescimento"

    if valor >= -5:
        return "🟡 Atenção"

    return "🔴 Crítico"


# ======================================================
# UPLOAD
# ======================================================

arquivo = st.file_uploader(
    "Upload da planilha SPI",
    type=["xlsx", "xls"]
)

if arquivo is not None:

    excel = pd.ExcelFile(arquivo)

    # ==========================================
    # FILTROS
    # ==========================================

    modulo = st.sidebar.selectbox(
        "Módulo",
        [
            "Volume",
            "Premium"
        ]
    )

    semana = st.sidebar.selectbox(
        "Semana",
        [
            "w37",
            "w38",
            "w39",
            "w40"
        ],
        index=3
    )

    periodo = st.sidebar.selectbox(
        "Indicador",
        [
            "WoW",
            "MTD",
            "QTD",
            "YTD"
        ]
    )

    cobertura = st.sidebar.selectbox(
        "Cobertura",
        [
            "Todos",
            "Promotores",
            "Sem Cobertura"
        ]
    )

    # ==========================================
    # PROMOTORES
    # ==========================================

    aba_promotores = next(
        aba
        for aba in excel.sheet_names
        if "promotor" in aba.lower()
    )

    promotores = pd.read_excel(
        arquivo,
        sheet_name=aba_promotores
    )

    cidade_promotor = detectar_coluna(
        promotores,
        "cidade"
    )

    supervisor_col = detectar_coluna(
        promotores,
        "supervisor"
    )

    hc_col = detectar_coluna(
        promotores,
        "hc"
    )

    # ==========================================
    # DADOS
    # ==========================================

    aba_dados = next(
        aba
        for aba in excel.sheet_names
        if (
            modulo.lower() in aba.lower()
            and
            semana.lower() in aba.lower()
        )
    )

    dados = pd.read_excel(
        arquivo,
        sheet_name=aba_dados
    )

    cidade_volume = detectar_coluna(dados, "city")

    if cidade_volume is None:

        st.error(
            "Coluna Act City não encontrada"
        )

        st.stop()

    # ==========================================
    # NORMALIZAÇÃO
    # ==========================================

    dados[cidade_volume] = (
        dados[cidade_volume]
        .apply(normalizar)
    )

    dados[cidade_volume] = (
        dados[cidade_volume]
        .apply(normalizar)
        .str.title()
    )

    # ==========================================
    # CONVERSÕES
    # ==========================================

    dados["L7D"] = pd.to_numeric(
        dados["L7D"],
        errors="coerce"
    )

    dados[periodo] = pd.to_numeric(
        dados[periodo]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    )

    # ==========================================
    # FILTRO CIDADES RELEVANTES
    # ==========================================

    dados = dados[
        dados["L7D"] >= 100
    ]

    promotores[cidade_promotor] = (
        promotores[cidade_promotor]
        .apply(normalizar)
        .str.title()
    )

    if cobertura == "Promotores":

        dados = dados[
            dados[cidade_volume]
            .isin(cidades_promotor)
        ]

    elif cobertura == "Sem Cobertura":

        dados = dados[
            ~dados[cidade_volume]
            .isin(cidades_promotor)
        ]

    # ==========================================
    # MERGE
    # ==========================================

    dados = dados.merge(
        promotores,
        left_on=cidade_volume,
        right_on=cidade_promotor,
        how="left"
    )
    correcoes_supervisor = {
        "AMERICANA": "Amanda",
        "HORTOLANDIA": "Amanda",
        "ITU": "Rafael",
        "SUMARE": "Amanda",
        "BEBEDOURO": "Alan",
        "REGISTRO": "William",
        "EMBU DAS ARTES": "William",
        "CARAGUATATUBA": "William",
        "BRAGANCA PAULISTA": "Amanda"
    }

    for cidade, supervisor in correcoes_supervisor.items():

        mask = (
            dados[cidade_volume]
            .str.upper()
            == cidade
        )

        dados.loc[
            mask,
            "Supervisor"
        ] = supervisor

        dados.loc[
            mask,
            "Qt HC"
        ] = 0

        dados["Status SPI"] = (
            dados[periodo]
            .apply(classificar_spi)
        )

    # ==========================================
    # KPIs
    # ==========================================

    st.header(
        f"📈 {modulo}"
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Cidades",
        len(dados)
    )

    c2.metric(
        "L7D Total",
        int(dados["L7D"].sum())
    )

    c3.metric(
        "HC Total",
        int(promotores[hc_col].sum())
    )

    c4.metric(
        "Supervisores",
        promotores[supervisor_col].nunique()
    )

    c5.metric(
        "Cobertura",
        cobertura
    )

    st.divider()

    # ==========================================
    # SEMÁFORO
    # ==========================================

    st.subheader(
        "🚦 Semáforo SPI"
    )

    s1, s2, s3 = st.columns(3)

    s1.metric(
        "🟢 Crescimento",
        len(
            dados[
                dados["Status SPI"]
                ==
                "🟢 Crescimento"
            ]
        )
    )

    s2.metric(
        "🟡 Atenção",
        len(
            dados[
                dados["Status SPI"]
                ==
                "🟡 Atenção"
            ]
        )
    )

    s3.metric(
        "🔴 Crítico",
        len(
            dados[
                dados["Status SPI"]
                ==
                "🔴 Crítico"
            ]
        )
    )

    # ==========================================
    # TOP 10
    # ==========================================

    colunas = [
        cidade_volume,
        "Supervisor",
        "Qt HC",
        "L7D",
        periodo
    ]

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            f"🚨 Top 10 Quedas - {periodo}"
        )

        st.dataframe(
            dados
            .sort_values(
                periodo,
                ascending=True
            )[colunas]
            .head(10),
            use_container_width=True
        )

    with col2:

        st.subheader(
            f"🚀 Top 10 Evoluções - {periodo}"
        )

        st.dataframe(
            dados
            .sort_values(
                periodo,
                ascending=False
            )[colunas]
            .head(10),
            use_container_width=True
        )

    # ==========================================
    # TOP 15
    # ==========================================

    st.subheader(
        f"🏙️ Top 15 - {periodo}"
    )

    fig_top = px.bar(
        dados.sort_values(
            periodo,
            ascending=False
        ).head(15),
        x=cidade_volume,
        y=periodo,
        color=periodo
    )

    st.plotly_chart(
        fig_top,
        use_container_width=True
    )

    # ==========================================
    # SUPERVISORES
    # ==========================================

    ranking = (
        dados
        .groupby(supervisor_col)[periodo]
        .mean()
        .reset_index()
        .sort_values(
            periodo,
            ascending=False
        )
    )

    st.subheader(
        "👥 Ranking Supervisores"
    )

    fig_sup = px.bar(
        ranking,
        x=supervisor_col,
        y=periodo,
        color=periodo
    )

    st.plotly_chart(
        fig_sup,
        use_container_width=True
    )

    # ==========================================
    # HC
    # ==========================================

    st.subheader(
        "🥧 Distribuição HC"
    )

    hc = (
        promotores
        .groupby(supervisor_col)[hc_col]
        .sum()
        .reset_index()
    )

    fig_hc = px.pie(
        hc,
        names=supervisor_col,
        values=hc_col
    )

    st.plotly_chart(
        fig_hc,
        use_container_width=True
    )

    # ==========================================
    # CIDADES CRÍTICAS
    # ==========================================

    criticas = dados[
        dados["Status SPI"]
        == "🔴 Crítico"
    ]

    st.subheader(
        "🚨 Cidades Críticas"
    )

    st.dataframe(
        criticas[colunas],
        use_container_width=True
    )