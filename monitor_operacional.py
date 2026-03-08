import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from streamlit_autorefresh import st_autorefresh
import datetime

# 1. ATUALIZAÇÃO AUTOMÁTICA (5 minutos)
st_autorefresh(interval=5 * 60 * 1000, key="datarefresh")

st.set_page_config(page_title="SECAD | Resultado Geral", layout="wide")

# Estilização dos KPIs
st.markdown("""
<style>

/* 🔹 Fundo da página */
[data-testid="stAppViewContainer"] {
    background-color: #0e1117;
}

[data-testid="stMain"] {
    background-color: #0e1117;
}

/* 🔹 Ajusta padding dos containers com border=True */
div[data-testid="stVerticalBlockBorderWrapper"] {
    padding: 6px 12px;
}

div[data-testid="srVerticalBlock"] > div {
    margin-top: 0rem !important;
    margin-bottom: 0rem !important
}                    

/* 🔹 Compacta os KPIs (st.metric) */
[data-testid="metric-container"] {
    padding-top: 4px;
    padding-bottom: 4px;
}

/* 🔹 Colunas dos KPIs alinhadas à esquerda */
[data-testid="column"] {
    display: flex;
    justify-content: flex-start;
    text-align: left;
    padding: 0px 5px !important;
    width: fit-content !important;
    min-width: min-content !important;
}

/* 🔹 Remove centralização forçada do metric */
[data-testid="stMetric"] {
    width: fit-content;
    margin-left: 0;
    margin-right: 0;
}

/* 🔹 Valor do KPI */
[data-testid="stMetricValue"] {
    font-size: 36px !important;
    font-weight: 800 !important;
    color: #6898f1 !important;
}

/* 🔹 Label do KPI */
[data-testid="stMetricLabel"] {
    font-size: 24px;
    color: #ffffff !important;
    font-weight: 700;
    letter-spacing: 0.5px;
}

/* 🔹 Texto de última atualização */
.ultima-atualizacao {
    font-size: 12.5px;
    opacity: 0.85;
    color: #cfd8dc;
    margin-top: -0.4rem;
    margin-bottom: 1.2rem;
}

h1, h2, h3{
    color: #ffffff !important;
}

/* 🔹 Sobe o header da página */
[data-testid="stMainBlockContainer"] {
    padding-top: 0.8rem;
}

</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_engine():
    user = *****
    password = ******
    host = *****
    port = *****
    database = *****
    password_encoded = quote_plus(password)
    return create_engine(f"postgresql+psycopg2://{user}:{password_encoded}@{host}:{port}/{database}")

# --- QUERY ATUALIZADA (Focada em Áreas) ---
QRY_VENDAS = """
WITH sales_data AS (
    SELECT 
        p.product_name,
        TO_CHAR(DATE_TRUNC('hour', s.purchase_datetime), 'HH24:MI') AS hr,

        CASE 
            WHEN pr.area ~* 'mental' THEN 'Psychology'
            WHEN pr.area IS NOT NULL THEN pr.area
            ELSE 'Other Areas'
        END AS area,

        si.value * s.total_value / NULLIF(
            SUM(si.value) OVER (PARTITION BY s.purchase_id), 0
        ) AS value,

        CASE
            WHEN s.seller_id IS NULL THEN 'eCommerce'
            WHEN LEFT(s.seller_id::text,1) = '8' THEN 'Representatives'
            WHEN LEFT(s.seller_id::text,1) = 'R' THEN 'Renewal'
            ELSE 'Call Center'
        END AS channel,

        DATE(s.purchase_datetime) AS data

    FROM sales.purchase s
    LEFT JOIN sales.purchase_items si 
        ON s.purchase_id = si.purchase_id
    LEFT JOIN sales.products p 
        ON si.product_id = p.product_id
    LEFT JOIN sales.requests r 
        ON s.request_id = r.request_id
    LEFT JOIN sales.customers c 
        ON s.customer_id = c.customer_id
    LEFT JOIN business.programs pr 
        ON p.product_name = pr.program

    WHERE DATE(s.purchase_datetime) >= CURRENT_DATE - INTERVAL '6 months'
    AND r.environment = 'production'
    AND LOWER(c.customer_name) NOT LIKE '%test%'
)

SELECT 
    area,
    data,
    hr,
    COUNT(*) AS total_sales,
    SUM(value) AS revenue
FROM sales_data
WHERE channel IN ('Call Center')
GROUP BY area, data, hr
ORDER BY revenue DESC;
"""

QRY_OPERACIONAL = """
WITH ranked_calls AS (
    SELECT
        RIGHT(phone_number,11) AS phone,

        ROW_NUMBER() OVER (
            PARTITION BY RIGHT(phone_number,11)
            ORDER BY call_start DESC
        ) AS rn,

        CASE
            WHEN source_table ~* 'mental|psychology' THEN 'Psychology'
            WHEN source_table ~* 'multi' THEN 'Multi'
            WHEN source_table ~* 'physio' THEN 'Physiotherapy'
            WHEN source_table ~* 'nursing' THEN 'Nursing'
            WHEN source_table ~* 'medical' THEN 'Medicine'
            WHEN source_table ~* 'nutrition' THEN 'Nutrition'
            WHEN source_table ~* 'veterinary' THEN 'Veterinary'
            WHEN source_table ~* 'pediatric' THEN 'Pediatrics'
            WHEN source_table ~* 'psychiatry' THEN 'Psychiatry'
            ELSE 'Other Areas'
        END AS area,

        CASE
            WHEN EXTRACT(EPOCH FROM wrap_duration) > 0 THEN 1
            ELSE 0
        END AS answered,

        DATE(call_start) AS data

    FROM operations.call_center_calls
    WHERE call_start::date >= CURRENT_DATE - INTERVAL '6 months'
)

SELECT
    area,
    data,
    COUNT(*) AS attempts,
    SUM(answered) AS answered_calls
FROM ranked_calls
WHERE rn = 1
GROUP BY area, data;


"""

# --- CARREGAMENTO ---
try:
    engine = get_engine()
    df_vendas = pd.read_sql(text(QRY_VENDAS), engine)
    df_vendas['data'] = pd.to_datetime(df_vendas['data'],errors='coerce')
    df_operacional = pd.read_sql(text(QRY_OPERACIONAL), engine)
    df_operacional['data'] = pd.to_datetime(df_operacional['data'], errors='coerce')
except Exception as e:
    st.error(f"Erro na conexão: {e}")
    df_vendas = pd.DataFrame()

# --- SIDEBAR ---
areas_disponiveis = df_vendas['area'].unique().tolist() if not df_vendas.empty else []

df_filtrado = df_vendas[df_vendas['area'].isin(areas_disponiveis)] if not df_vendas.empty else pd.DataFrame()
df_operacional_filtrado = df_operacional[df_operacional['area'].isin(areas_disponiveis)] if not df_operacional.empty else pd.DataFrame()

# --- TELA PRINCIPAL ---
st.title("📊SECAD|Monitor Operacional")

st.markdown(
    f"""
    <div class="ultima-atualizacao">
        🕒 <strong>Última Atualização:</strong> {datetime.datetime.now().strftime('%H:%M:%S')}
    </div>
    """,
    unsafe_allow_html=True
)

### bases operacionais e financeiras de hoje
hoje = pd.to_datetime(datetime.datetime.now().date())
df_financeiro_hoje = df_filtrado[df_filtrado['data'].dt.normalize() == hoje]
df_operacional_hoje = df_operacional_filtrado.loc[df_operacional_filtrado['data'].dt.normalize() == hoje].copy()



## Média historica - LOCALIZAÇÃO
df_hist = (
    df_operacional_filtrado.loc[
        (df_operacional_filtrado['data'] >= hoje - pd.DateOffset(months=5)) &
        (df_operacional_filtrado['data'] < hoje)
    ]
    .copy()
)
df_hist['mes'] = df_hist['data'].dt.to_period('M')
df_hist_mensal =(
    df_hist
    .groupby('mes',as_index=False)
    .agg(
        tentativas=('tentativas','sum'),
        atendidas=('atendidas','sum')
    )
)

df_hist_mensal['tx_loc'] = (
    df_hist_mensal['atendidas'] /
    df_hist_mensal['tentativas'] * 100
)

taxa_hist = df_hist_mensal['tx_loc'].mean()


if not df_filtrado.empty:
    
    #KPI's de Performance Mensal -  INICIO
    with st.container(border=False):
        st.markdown("<h3 style='margin-bottom: 0.6rem;'>📈 Performance Mensal</h3>", 
                    unsafe_allow_html=True
                )
        m1,m2,m3 = st.columns([1.5,2.2,10],gap='small')

        with m1:
            st.metric('Vendas|Mês',int(df_filtrado['qtd_vendas'].sum()))
        with m2:
            st.metric('Receita|Mês',f"R${df_filtrado['total_valor'].sum():,.2f}")
        with m3:
            vendas_mês = df_filtrado['qtd_vendas'].sum()
            ticket = (df_filtrado['total_valor'].sum() / vendas_mês) if vendas_mês > 0 else 0
            st.metric('Ticket Médio (Mês)', f"R$ {ticket:,.2f}")
    #KPI's de Performance Mensal -  FIM

    #KPIs de hoje - INICIO

    hoje = pd.to_datetime(datetime.datetime.now().date())
    st.subheader(f'Resultado Operacional - {hoje.strftime("%d/%m/%Y")}',text_alignment='left')     

    with st.container(border=False):
        col_vendas, col_receita, col_ticket, = st.columns([1.5,2.2,10],gap='small')
        
        financeiro_hoje = df_financeiro_hoje.groupby('area').agg(
            receita = ('total_valor','sum'),
            vendas = ('qtd_vendas','sum')
        ).reset_index()

        
        vendas_total = financeiro_hoje['vendas'].sum()
        receita_total = financeiro_hoje['receita'].sum()
        ticket = (receita_total / vendas_total) if vendas_total > 0 else 0

        with col_vendas:
                col_vendas.metric('Vendas', int(vendas_total))
        with col_receita:
                col_receita.metric('Receita', f"R$ {receita_total:,.2f}")
        with col_ticket:
                col_ticket.metric('Ticket Médio', f"R$ {ticket:,.2f}")                       
        
        col_tentativas, col_atendidas, col_taxa = st.columns([1.5,2.2,10],gap='small')

        tentativas = int(df_operacional_hoje['tentativas'].sum())
        atendidas = int(df_operacional_hoje['atendidas'].sum())
        taxa = (atendidas / tentativas * 100) if tentativas > 0 else 0
        dif_loc = taxa - taxa_hist
        sinal = "▲" if dif_loc >= 0 else "▼"
        cor = "green" if dif_loc >= 0 else "red"

        if taxa < 5:
            cor_taxa = "#ff4d4d"   # vermelho
        elif taxa < 10:
            cor_taxa = "#ffa500"   # laranja
        else:
            cor_taxa = "#2ecc71"

        delta_txt = f"{sinal} {abs(dif_loc):.2f} pp vs média (5m)"

        with col_tentativas:
                col_tentativas.metric('Tentativas', tentativas)
        with col_atendidas:
                col_atendidas.metric('Atendidas', atendidas)
        with col_taxa:
            st.markdown(
                f"""
                <div style="padding-top:6px">
                    <div style="font-size:14px; color:#ffffff;">
                        Taxa de Localização
                    </div>
                    <div style="font-size:36px; font-weight:700; color:{cor_taxa}; line-height:1;">
                        {taxa:.2f}%
                    </div>
                    <div style="font-size:12px; color:{cor}; margin-top:4px;">
                        {delta_txt}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    #KPIs de hoje - FIM            


    # GRAFICOs
    col_vendas, col_atendimento = st.columns([1, 1], gap='medium',border=True)

    with col_vendas:
        st.subheader("💰Venda por Área")

        fig = go.Figure()

        # 1. Camada Principal: Barras com o Valor (R$) Fora
        fig.add_trace(go.Bar(
            x=financeiro_hoje['area'],
            y=financeiro_hoje['receita'],
            text=financeiro_hoje['receita'],
            texttemplate='<b>R$ %{text:,.2f}</b>',
            textposition='outside',
            textfont=dict(size=16, color='white', family='Arial'),
            marker_color="#4b84ed",
            name='Receita'
        ))

        # 2. Camada de "Sobreposição": Texto da Quantidade na Base (Inside)
        fig.add_trace(go.Bar(
            x=financeiro_hoje['area'],
            y=financeiro_hoje['vendas'],
            text=financeiro_hoje['vendas'],
            texttemplate='%{text}',
            textposition='inside',
            insidetextanchor='end', 
            textfont=dict(size=16, color="#FFFFFF", family='Arial'),
            marker_color="rgba(0,0,0,0)", 
            showlegend=False,
            hoverinfo='skip' 
        ))

        # 3. Ajustes de Layout e Estética
        fig.update_layout(
            showlegend=False,
            barmode='overlay', # Importante: coloca uma camada exatamente sobre a outra
            yaxis=dict(visible=False),
            xaxis=dict(
                title=None,
                tickfont=dict(size=16, color='#ffffff')
            ),
            height=250,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=50, b=20), # Aumentei o topo para o valor de fora não cortar
        )

        st.plotly_chart(fig, use_container_width=True,height=400)

    with col_atendimento:

        df_operacional_hoje['tx_loc'] = (
            df_operacional_hoje['atendidas'] /
            df_operacional_hoje['tentativas'] * 100
        ).round(2)

        st.subheader("Atendimentos por Área")

        fig = go.Figure()

        # 1. Camada Principal: Texto de Quantidade na base (Fora) | TENTATIVAS
        fig.add_trace(go.Bar(
            x=df_operacional_hoje['area'],
            y=df_operacional_hoje['tentativas'],
            text=df_operacional_hoje['tentativas'],
            texttemplate='<b>%{text}</b>',
            textposition='outside',
            textfont=dict(size=16, color='#ffffff', family='Arial'),
            marker_color="#3e7bed",
            name='Tentativas',
            customdata=df_operacional_hoje['tx_loc'],
            hovertemplate=
                '<b>Área:</b> %{x}<br>' +
                '<b>Tentativas:</b> %{y}<br>' +
                '<b>Tx Localização:</b> %{customdata[0]}%<extra></extra>'
        ))

        # 2. Camada de "Sobreposição": Texto da Quantidade na Base (Inside) | ATENDIDAS
        fig.add_trace(go.Bar(
            x=df_operacional_hoje['area'],
            y=df_operacional_hoje['atendidas'],
            text=df_operacional_hoje['atendidas'],
            texttemplate='%{text}',
            textposition='outside',
            textfont=dict(size=16, color="#FFFFFF", family='Arial'),
            marker_color="#93ADE6",
            opacity=0.85, 
            name='Atendidas',
            customdata=df_operacional_hoje[['tx_loc']],
            hovertemplate=
                '<b>Área:</b> %{x}<br>' +
                '<b>Atendidas:</b> %{y}<br>' +
                '<b>Tx Localização:</b> %{customdata[0]}%<extra></extra>' 
        ))

        # 3. Ajustes de Layout e Estética
        fig.update_layout(
            barmode='overlay', # Importante: coloca uma camada exatamente sobre a outra
            yaxis=dict(visible=False),
            xaxis=dict(
                title=None,
                tickfont=dict(size=16, color='#ffffff')
            ),
            height=250,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.05,
                xanchor='center',
                x=0.5,
                font=dict(size=16, color='#ffffff')
            ),

            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=50, b=20),
            hovermode='x unified'

        )

        st.plotly_chart(fig, use_container_width=True,height=400)

    col_vendas_hora = st.columns([1])

    with col_vendas_hora[0]:
        st.subheader("💰 Venda por Hora")
        
        fig = go.Figure()

        hora_venda = df_financeiro_hoje.groupby('hr').agg(
                qtd_vendas = ('qtd_vendas','sum')
        ).reset_index()


        fig.add_trace(go.Scatter(
            x=hora_venda['hr'],
            y=hora_venda['qtd_vendas'],
            text=hora_venda['qtd_vendas'],
            texttemplate='<b>%{text:}</b>',
            textposition='top center',
            mode='lines+markers+text',
            textfont=dict(size=16, color='#ffffff', family='Arial'),
            line=dict(color='#4b84ed',width=3),
            marker=dict(color='#4b84ed',size=8,),
        ))

        fig.update_layout(
            showlegend=False,
            barmode='overlay',
            yaxis=dict(visible=False),
            xaxis=dict(
                title=None,
                tickfont=dict(size=16,color='#ffffff')
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=50,b=20)
        )


        st.plotly_chart(fig,use_container_width=True)    



else:
    st.warning("Aguardando dados de vendas para o dia de hoje...")
