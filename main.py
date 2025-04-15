import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import io, os, math

# Import dos módulos criados
from data_loader import download_file_from_gdrive, validate_dataframe
from style import COLORS, get_css
from metrics import format_number, format_percent, custom_round

# Configuração da página
st.set_page_config(
    page_title="Dashboard Comercial - Budget vs Logcomex vs iTracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Seleção de Tema na Sidebar ---
st.markdown(get_css("Clean"), unsafe_allow_html=True)

# Cabeçalho do dashboard (sem alteração dos padrões institucionais: laranja e branco)
st.markdown("""
    <div class="titulo-dashboard-container">
        <h1 class="titulo-dashboard">Dashboard de análise comercial de clientes</h1>
        <p class="subtitulo-dashboard">Monitoramento em tempo real do desempenho comercial</p>
    </div>
""", unsafe_allow_html=True)
st.markdown(f"""<hr style="border-top: 3px solid {COLORS['primary']}; margin: 20px 0;">""", unsafe_allow_html=True)

# Data atual para o footer
current_date = datetime.now().strftime("%d de %B de %Y")

# --- Carregamento dos dados ---
df = download_file_from_gdrive()
if df is None:
    st.error("Não foi possível carregar os dados do Google Sheets.")
    st.stop()

# Validação dos dados
df = validate_dataframe(df)

# Pré-processamento dos dados
df = df[df['Cliente'].notna() & (df['Cliente'] != "undefined")]
df['Cliente'] = df['Cliente'].str.upper()

numeric_cols = ['MÊS', 'BUDGET', 'Importação', 'Exportação', 'Cabotagem', 'Quantidade_iTRACKER']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# --- Sidebar: Filtros ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtros de Análise")
meses_map = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
meses_disponiveis = sorted(df['MÊS'].unique())
mes_selecionado = st.sidebar.multiselect(
    "Selecione o(s) mês(es):",
    options=meses_disponiveis,
    format_func=lambda x: meses_map.get(x, x),
    default=[meses_disponiveis[0]] if meses_disponiveis else []
)
clientes_disponiveis = sorted(df['Cliente'].unique())
cliente_selecionado = st.sidebar.multiselect(
    "Selecione o(s) cliente(s):",
    options=clientes_disponiveis
)
if st.sidebar.button("Limpar Filtros"):
    mes_selecionado = []
    cliente_selecionado = []
st.sidebar.markdown("---")
show_detailed_table = st.sidebar.checkbox("Mostrar tabela detalhada", value=True)
chart_height = st.sidebar.slider("Altura dos gráficos", 400, 800, 500, 50)

if mes_selecionado and cliente_selecionado:
    filtered_df = df[(df['MÊS'].isin(mes_selecionado)) & (df['Cliente'].isin(cliente_selecionado))]
elif mes_selecionado:
    filtered_df = df[df['MÊS'].isin(mes_selecionado)]
elif cliente_selecionado:
    filtered_df = df[df['Cliente'].isin(cliente_selecionado)]
else:
    filtered_df = df.copy()

if mes_selecionado or cliente_selecionado:
    filtros_ativos = []
    if mes_selecionado:
        meses_texto = [meses_map.get(m, m) for m in mes_selecionado]
        filtros_ativos.append(f"Meses: {', '.join(map(str, meses_texto))}")
    if cliente_selecionado:
        filtros_ativos.append(f"Clientes: {', '.join(cliente_selecionado)}")
    st.markdown(f"<div style='background-color:#E3F2FD;padding:10px;border-radius:5px;margin-bottom:20px;'>"
                f"<b>Filtros ativos:</b> {' | '.join(filtros_ativos)}</div>", unsafe_allow_html=True)

# --- Seção de KPIs ---
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("<h3 class='section-title'>VISÃO GERAL</h3>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
total_budget = filtered_df['BUDGET'].sum()
with col1:
    st.markdown(f"""
    <div class='kpi-card'>
        <p class='kpi-title'>💰 TOTAL BUDGET</p>
        <p class='kpi-value'>{format_number(total_budget)}</p>
    </div>
    """, unsafe_allow_html=True)
total_oportunidades = filtered_df['Importação'].sum() + filtered_df['Exportação'].sum() + filtered_df['Cabotagem'].sum()
with col2:
    st.markdown(f"""
    <div class='kpi-card'>
        <p class='kpi-title'>🧭 TOTAL OPORTUNIDADES</p>
        <p class='kpi-value'>{format_number(total_oportunidades)}</p>
    </div>
    """, unsafe_allow_html=True)
total_itracker = filtered_df['Quantidade_iTRACKER'].sum()
with col3:
    st.markdown(f"""
    <div class='kpi-card'>
        <p class='kpi-title'>🚚 TOTAL REALIZADO (SYSTRACKER)</p>
        <p class='kpi-value'>{format_number(total_itracker)}</p>
    </div>
    """, unsafe_allow_html=True)
with col4:
    performance_val = (total_itracker / total_budget) * 100 if total_budget > 0 else 0
    st.markdown(f"""
    <div class='kpi-card'>
        <p class='kpi-title'>🎯 PERFORMANCE VS BUDGET (Até Hoje)</p>
        <p class='kpi-value'>{format_percent(performance_val)}</p>
    </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- Gráfico Principal: GAP de Atendimento ---
if not filtered_df.empty:
    current_month = datetime.now().month
    df_current = filtered_df[filtered_df['MÊS'] == current_month]
    if not df_current.empty:
        df_gap = df_current.groupby("Cliente", as_index=False).agg({
            "Target Acumulado": "sum",
            "Quantidade_iTRACKER": "sum",
            "Gap de Realização": "sum"
        })
        df_gap['Gap de Realização'] = df_gap['Gap de Realização'].apply(custom_round)
        df_gap = df_gap.sort_values("Gap de Realização", ascending=False)
        df_gap_top = df_gap.head(15)
        
        fig_gap = px.bar(
            df_gap_top,
            x="Gap de Realização",
            y="Cliente",
            orientation="h",
            text="Gap de Realização",
            color="Gap de Realização",
            color_continuous_scale=px.colors.sequential.Reds,
            labels={"Gap de Realização": "Gap de Atendimento"},
            title="CLIENTES COM MAIOR GAP DE ATENDIMENTO (MÊS CORRENTE)"
        )
        fig_gap.update_layout(
            yaxis=dict(autorange="reversed"),
            height=chart_height,
            margin=dict(l=60, r=60, t=40, b=80),
            legend=dict(orientation='h', y=-0.25, x=0.5, xanchor='center'),
            plot_bgcolor="white"
        )
        fig_gap.update_traces(texttemplate='%{text}', textposition='outside')
        
        st.markdown("<div class='section'><h3 class='section-title'>🚨 CLIENTES COM MAIOR GAP VS TARGET ACUMULADO</h3></div>", unsafe_allow_html=True)
        st.plotly_chart(fig_gap, use_container_width=True)
        
        with st.expander("VER RAZÃO DO CÁLCULO DESTE GRÁFICO"):
            st.markdown("""
            **DETALHAMENTO DO CÁLCULO:**
            - **FILTRAGEM:** Dados referentes ao MÊS CORRENTE.
            - **AGRUPAMENTO:** Soma dos valores de TARGET ACUMULADO, REALIZADO SYSTRACKER e GAP DE REALIZAÇÃO.
            - **ARREDONDAMENTO:** Aplicação de `custom_round` no GAP.
            - **ORDENAÇÃO:** Ordenação decrescente pelo GAP.
            """)
    else:
        st.info("NÃO EXISTEM DADOS PARA O MÊS CORRENTE PARA ANÁLISE DE GAP.")

# --- Gráfico 2: Aproveitamento de Oportunidades por Cliente ---
if not filtered_df.empty:
    opp_df = filtered_df[(filtered_df['Importação']+filtered_df['Exportação']+filtered_df['Cabotagem']) > 0].copy()
    if not opp_df.empty:
        st.markdown("<h4 class='sub-title'>APROVEITAMENTO DE OPORTUNIDADES POR CLIENTE</h4>", unsafe_allow_html=True)
        df_graph2 = opp_df.groupby('Cliente', as_index=False).agg({
            'Importação': 'sum',
            'Exportação': 'sum',
            'Cabotagem': 'sum',
            'Quantidade_iTRACKER': 'sum'
        })
        df_graph2['Total_Oportunidades'] = df_graph2[['Importação', 'Exportação', 'Cabotagem']].sum(axis=1)
        df_graph2['Aproveitamento'] = (df_graph2['Quantidade_iTRACKER'] / df_graph2['Total_Oportunidades']) * 100
        df_graph2 = df_graph2.sort_values('Aproveitamento', ascending=False)
        if len(df_graph2) > 15:
            df_graph2 = df_graph2.head(15)
        fig2 = px.bar(
            df_graph2,
            x='Cliente',
            y='Aproveitamento',
            color='Aproveitamento',
            color_continuous_scale=px.colors.sequential.Blues,
            text_auto='.1f',
            labels={'Aproveitamento': 'TAXA DE APROVEITAMENTO (%)'},
            custom_data=['Total_Oportunidades', 'Quantidade_iTRACKER']
        )
        fig2.update_traces(
            texttemplate='%{y:.1f}%',
            textposition='outside',
            hovertemplate=(
                '<b>CLIENTE:</b> %{x}<br>'
                '<b>TAXA DE APROVEITAMENTO:</b> %{y:.1f}%<br>'
                '<b>TOTAL OPORTUNIDADES:</b> %{customdata[0]:,.0f}<br>'
                '<b>REALIZADO:</b> %{customdata[1]:,.0f}<extra></extra>'
            )
        )
        fig2.update_layout(
            xaxis_title='CLIENTE',
            yaxis_title='TAXA DE APROVEITAMENTO (%)',
            coloraxis_colorbar=dict(title='APROVEITAMENTO (%)'),
            height=chart_height,
            template="plotly",
            margin=dict(l=60, r=60, t=30, b=60),
            xaxis=dict(tickangle=-45),
            yaxis=dict(range=[0, min(150, df_graph2['Aproveitamento'].max() * 1.1)])
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        with st.expander("VER RAZÃO DO CÁLCULO DESTE GRÁFICO"):
            st.markdown("""
            **DETALHAMENTO DO CÁLCULO:**
            - **FILTRAGEM:** Considera apenas os CLIENTES com oportunidades (IMPORTAÇÃO + EXPORTAÇÃO + CABOTAGEM > 0).
            - **AGRUPAMENTO:** Soma de IMPORTAÇÃO, EXPORTAÇÃO, CABOTAGEM e REALIZADO SYSTRACKER.
            - **TOTAL DE OPORTUNIDADES:** Soma das três categorias.
            - **APROVEITAMENTO:** (REALIZADO SYSTRACKER / TOTAL DE OPORTUNIDADES) * 100.
            """)
        
        media_aproveitamento = df_graph2['Aproveitamento'].mean()
        melhor_cliente = df_graph2.iloc[0]['Cliente']
        melhor_aproveitamento = df_graph2.iloc[0]['Aproveitamento']
        
        st.markdown(f"""
        <div style='background-color:{COLORS['background']}; padding:10px; border-radius:5px; margin-top:10px;'>
            <h5 style='margin-top:0'>📊 INSIGHTS - APROVEITAMENTO</h5>
            <ul>
                <li>A TAXA MÉDIA DE APROVEITAMENTO DE OPORTUNIDADES É DE {media_aproveitamento:.1f}%</li>
                <li>O CLIENTE COM MELHOR APROVEITAMENTO É <b>{melhor_cliente}</b> COM {melhor_aproveitamento:.1f}%</li>
                <li>{"A MAIORIA DOS CLIENTES ESTÁ ABAIXO DA META MÍNIMA DE 50%" if media_aproveitamento < 50 else "A MAIORIA DOS CLIENTES ATINGE PELO MENOS A META MÍNIMA DE 50%"}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("SEM DADOS DE OPORTUNIDADES DISPONÍVEIS PARA OS FILTROS SELECIONADOS.")
        
# ---  Gráfico 3: CLIENTES FORA DO BUDGET COM OPERAÇÕES REALIZADAS --- 
df_no_budget = filtered_df[
    ((filtered_df['BUDGET'].isna()) | (filtered_df['BUDGET'] == 0)) &
    (filtered_df['Quantidade_iTRACKER'] > 0)
]

if not df_no_budget.empty:
    df_graph = df_no_budget.groupby("Cliente", as_index=False)['Quantidade_iTRACKER'].sum()
    df_graph = df_graph.sort_values('Quantidade_iTRACKER', ascending=False).head(15)

    fig_no_budget = px.bar(
        df_graph,
        x='Quantidade_iTRACKER',
        y='Cliente',
        orientation='h',
        text='Quantidade_iTRACKER',
        color='Quantidade_iTRACKER',
        color_continuous_scale=px.colors.sequential.Oranges,
        title="CLIENTES FORA DO BUDGET COM OPERAÇÕES REALIZADAS"
    )
    fig_no_budget.update_layout(
        height=chart_height,
        yaxis=dict(autorange="reversed"),
        margin=dict(l=60, r=30, t=40, b=60),
        plot_bgcolor="white"
    )
    fig_no_budget.update_traces(texttemplate='%{text}', textposition='outside')

    st.markdown("<h4 class='sub-title'>CLIENTES FORA DO BUDGET COM OPERAÇÕES REALIZADAS</h4>", unsafe_allow_html=True)
    st.plotly_chart(fig_no_budget, use_container_width=True)


# --- Gráfico 4: Performance vs Budget ---
if not filtered_df.empty:
    budget_df = filtered_df[filtered_df['BUDGET'] > 0].copy()
    if not budget_df.empty:
        st.markdown("<h4 class='sub-title'>PERFORMANCE VS BUDGET POR CLIENTE</h4>", unsafe_allow_html=True)
        df_graph3 = budget_df.groupby('Cliente', as_index=False).agg({
            'BUDGET': 'sum',
            'Quantidade_iTRACKER': 'sum'
        })
        df_graph3['Performance'] = (df_graph3['Quantidade_iTRACKER'] / df_graph3['BUDGET']) * 100
        df_graph3 = df_graph3.sort_values('Performance', ascending=False)
        if len(df_graph3) > 15:
            df_graph3 = df_graph3.head(15)
        df_graph3['Color'] = df_graph3['Performance'].apply(
            lambda x: COLORS['success'] if x >= 100 else (COLORS['warning'] if x >= 70 else COLORS['danger'])
        )
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=df_graph3['Performance'],
            y=df_graph3['Cliente'],
            orientation='h',
            marker_color=df_graph3['Color'],
            text=df_graph3['Performance'].apply(lambda x: f'{x:.1f}%'),
            hovertemplate='<b>%{y}</b><br>Performance: %{x:.1f}%<br>Budget: %{customdata[0]:,.0f}<br>Realizado: %{customdata[1]:,.0f}<extra></extra>',
            customdata=np.stack((df_graph3['BUDGET'], df_graph3['Quantidade_iTRACKER']), axis=-1)
        ))
        fig3.add_shape(
            type="line",
            x0=100,
            y0=-0.5,
            x1=100,
            y1=len(df_graph3)-0.5,
            line=dict(color="black", width=2, dash="dash")
        )
        fig3.add_shape(
            type="rect",
            x0=0,
            y0=-0.5,
            x1=70,
            y1=len(df_graph3)-0.5,
            line=dict(width=0),
            fillcolor="rgba(239, 83, 80, 0.1)",
            layer="below"
        )
        fig3.add_shape(
            type="rect",
            x0=70,
            y0=-0.5,
            x1=100,
            y1=len(df_graph3)-0.5,
            line=dict(width=0),
            fillcolor="rgba(255, 167, 38, 0.1)",
            layer="below"
        )
        fig3.add_shape(
            type="rect",
            x0=100,
            y0=-0.5,
            x1=df_graph3['Performance'].max() * 1.1,
            y1=len(df_graph3)-0.5,
            line=dict(width=0),
            fillcolor="rgba(102, 187, 106, 0.1)",
            layer="below"
        )
        fig3.add_annotation(
            x=35,
            y=len(df_graph3)-1,
            text="CRÍTICO (<70%)",
            showarrow=False,
            font=dict(color=COLORS['danger']),
            xanchor="center",
            yanchor="top"
        )
        fig3.add_annotation(
            x=85,
            y=len(df_graph3)-1,
            text="ATENÇÃO (70-100%)",
            showarrow=False,
            font=dict(color=COLORS['warning']),
            xanchor="center",
            yanchor="top"
        )
        fig3.add_annotation(
            x=min(150, df_graph3['Performance'].max() * 0.9),
            y=len(df_graph3)-1,
            text="META ATINGIDA (>100%)",
            showarrow=False,
            font=dict(color=COLORS['success']),
            xanchor="center",
            yanchor="top"
        )
        fig3.update_traces(textposition='inside')
        fig3.update_layout(
            xaxis_title='PERFORMANCE (%)',
            yaxis_title='CLIENTE',
            height=chart_height,
            template="plotly",
            margin=dict(l=60, r=30, t=30, b=40),
            xaxis=dict(range=[0, max(200, df_graph3['Performance'].max() * 1.1)])
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        with st.expander("VER RAZÃO DO CÁLCULO DESTE GRÁFICO"):
            st.markdown("""
            **DETALHAMENTO DO CÁLCULO:**
            - **FILTRAGEM:** Considera clientes com BUDGET > 0.
            - **AGRUPAMENTO:** Soma de BUDGET e REALIZADO SYSTRACKER por CLIENTE.
            - **PERFORMANCE:** (REALIZADO / BUDGET) * 100.
            - **CORES:** Definidas conforme thresholds.
            """)
        
        total_clientes = len(df_graph3)
        clientes_acima_meta = len(df_graph3[df_graph3['Performance'] >= 100])
        clientes_atencao = len(df_graph3[(df_graph3['Performance'] < 100) & (df_graph3['Performance'] >= 70)])
        clientes_critico = len(df_graph3[df_graph3['Performance'] < 70])
        
        st.markdown(f"""
        <div style='background-color:{COLORS['background']}; padding:10px; border-radius:5px; margin-top:10px;'>
            <h5 style='margin-top:0'>📊 INSIGHTS - PERFORMANCE</h5>
            <ul>
                <li>Dos {total_clientes} CLIENTES analisados:</li>
                <li><span style='color:{COLORS["success"]};'>✓ {clientes_acima_meta} CLIENTES ({clientes_acima_meta/total_clientes*100:.1f}%) ATINGEM OU SUPERAM A META</span></li>
                <li><span style='color:{COLORS["warning"]};'>⚠️ {clientes_atencao} CLIENTES ({clientes_atencao/total_clientes*100:.1f}%) ESTÃO EM ZONA DE ATENÇÃO (70-99%)</span></li>
                <li><span style='color:{COLORS["danger"]};'>❌ {clientes_critico} CLIENTES ({clientes_critico/total_clientes*100:.1f}%) ESTÃO EM SITUAÇÃO CRÍTICA (<70%)</span></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("SEM DADOS DE BUDGET DISPONÍVEIS PARA OS FILTROS SELECIONADOS.")
st.markdown("</div>", unsafe_allow_html=True)

# --- Gráfico 5: Comparativo Budget vs Realizado por Categoria ---
if not filtered_df.empty:
    st.markdown("<h4 class='sub-title'>COMPARATIVO BUDGET VS REALIZADO POR CATEGORIA</h4>", unsafe_allow_html=True)
    clientes_top = filtered_df.groupby('Cliente', as_index=False)['BUDGET'].sum()\
                    .sort_values('BUDGET', ascending=False)['Cliente'].head(15)
    df_top = filtered_df[filtered_df['Cliente'].isin(clientes_top)]
    df_grouped = df_top.groupby('Cliente', as_index=False).agg({
        'BUDGET': 'sum',
        'Importação': 'sum',
        'Exportação': 'sum',
        'Cabotagem': 'sum'
    })
    df_grouped['Total'] = df_grouped[['BUDGET', 'Importação', 'Exportação', 'Cabotagem']].sum(axis=1)
    df_grouped = df_grouped.sort_values('Total', ascending=False)
    df_melted = df_grouped.melt(
        id_vars='Cliente',
        value_vars=['BUDGET', 'Importação', 'Exportação', 'Cabotagem'],
        var_name='Categoria',
        value_name='Quantidade'
    )
    df_melted = df_melted[df_melted['Quantidade'] > 0]
    df_melted['Categoria_Label'] = df_melted['Categoria']
    
    fig = px.bar(
        df_melted,
        x='Cliente',
        y='Quantidade',
        color='Categoria',
        barmode='group',
        height=chart_height,
        color_discrete_map={
            'BUDGET': '#0D47A1',
            'Importação': '#00897B',
            'Exportação': '#F4511E',
            'Cabotagem': '#FFB300'
        },
        labels={'Quantidade': 'QTD. DE CONTAINERS'},
        custom_data=['Categoria_Label']
    )
    fig.update_traces(
        texttemplate='%{y:.0f}',
        textposition='outside',
        hovertemplate='<b>CLIENTE:</b> %{x}<br><b>CATEGORIA:</b> %{customdata[0]}<br><b>QTD.:</b> %{y:.0f}<extra></extra>'
    )
    fig.update_layout(
        xaxis=dict(title='CLIENTE', tickangle=-30),
        yaxis=dict(title='QTD. DE CONTAINERS', range=[0, df_melted['Quantidade'].max() * 1.1]),
        legend=dict(orientation='h', y=-0.25, x=0.5, xanchor='center'),
        margin=dict(l=60, r=40, t=20, b=100),
        template='plotly_white',
        bargap=0.25,
        title_text="",
        plot_bgcolor="white"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("VER RAZÃO DO CÁLCULO DESTE GRÁFICO"):
        st.markdown("""
        **DETALHAMENTO DO CÁLCULO:**
        - **AGRUPAMENTO:** Dados agrupados por CLIENTE com soma de BUDGET, IMPORTAÇÃO, EXPORTAÇÃO e CABOTAGEM.
        - **TOTAL:** Soma de todas as categorias.
        - Compara o BUDGET com o realizado.
        """)
else:
    st.info("SEM DADOS DISPONÍVEIS PARA O GRÁFICO DE COMPARATIVO APÓS APLICAÇÃO DOS FILTROS.")



# --- Tabela de Dados Detalhados ---
if show_detailed_table and not filtered_df.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-title'>DADOS DETALHADOS</h3>", unsafe_allow_html=True)
    if 'MÊS' in filtered_df.columns:
        detailed_df = filtered_df.sort_values(['Cliente', 'MÊS'])
    else:
        detailed_df = filtered_df.sort_values(['Cliente'])
    detailed_df['Mês_Nome'] = detailed_df['MÊS'].map(meses_map)
    detailed_df = detailed_df[[ 
        'Cliente', 'MÊS', 'Mês_Nome', 'BUDGET', 'Importação', 'Exportação', 'Cabotagem',
        'Target Acumulado', 'Quantidade_iTRACKER', 'Gap de Realização' 
    ]]
    detailed_df.columns = [
        'CLIENTE', 'MÊS (NÚM)', 'MÊS', 'BUDGET', 'IMPORTAÇÃO', 'EXPORTAÇÃO',
        'CABOTAGEM', 'TARGET ACUMULADO', 'REALIZADO (SYSTRACKER)', 'GAP DE REALIZAÇÃO'
    ]
    detailed_df = detailed_df.sort_values(['CLIENTE', 'MÊS (NÚM)'])
    cols = st.columns([3, 1])
    with cols[0]:
        search_term = st.text_input("BUSCAR CLIENTE", "")
    with cols[1]:
        sort_by = st.selectbox(
            "ORDENAR POR",
            options=["CLIENTE", "MÊS", "BUDGET", "REALIZADO (SYSTRACKER)", "GAP DE REALIZAÇÃO"],
            index=0
        )
    if search_term:
        detailed_df = detailed_df[detailed_df['CLIENTE'].str.contains(search_term.upper(), case=False)]
    if sort_by == "CLIENTE":
        detailed_df = detailed_df.sort_values(['CLIENTE', 'MÊS (NÚM)'])
    elif sort_by == "MÊS":
        detailed_df = detailed_df.sort_values(['MÊS (NÚM)', 'CLIENTE'])
    elif sort_by == "BUDGET":
        detailed_df = detailed_df.sort_values('BUDGET', ascending=False)
    elif sort_by == "REALIZADO (SYSTRACKER)":
        detailed_df = detailed_df.sort_values('REALIZADO (SYSTRACKER)', ascending=False)
    elif sort_by == "GAP DE REALIZAÇÃO":
        detailed_df = detailed_df.sort_values('GAP DE REALIZAÇÃO', ascending=False)
    detailed_df['REALIZADO (SYSTRACKER)'] = detailed_df['REALIZADO (SYSTRACKER)'].apply(lambda x: f'{x:.0f}')
    detailed_df['GAP DE REALIZAÇÃO'] = detailed_df['GAP DE REALIZAÇÃO'].apply(lambda x: f'{x:.1f}')
    st.dataframe(
        detailed_df,
        column_config={
            "CLIENTE": st.column_config.TextColumn("CLIENTE"),
            "MÊS": st.column_config.TextColumn("MÊS"),
            "BUDGET": st.column_config.NumberColumn("BUDGET", format="%d"),
            "IMPORTAÇÃO": st.column_config.NumberColumn("IMPORTAÇÃO", format="%d"),
            "EXPORTAÇÃO": st.column_config.NumberColumn("EXPORTAÇÃO", format="%d"),
            "CABOTAGEM": st.column_config.NumberColumn("CABOTAGEM", format="%d"),
            "TARGET ACUMULADO": st.column_config.NumberColumn("TARGET ACUMULADO", format="%d"),
            "REALIZADO (SYSTRACKER)": st.column_config.TextColumn("REALIZADO (SYSTRACKER)"),
            "GAP DE REALIZAÇÃO": st.column_config.TextColumn("GAP DE REALIZAÇÃO"),
        },
        use_container_width=True,
        height=500,
        hide_index=True
    )
    csv = detailed_df.to_csv(index=False)
    excel_buffer = io.BytesIO()
    detailed_df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_data = excel_buffer.getvalue()
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "📥 BAIXAR CSV",
            csv,
            "dados_detalhados.csv",
            "text/csv",
            key='download-csv'
        )
    with col_dl2:
        st.download_button(
            "📥 BAIXAR EXCEL",
            excel_data,
            "dados_detalhados.xlsx",
            "application/vnd.ms-excel",
            key='download-excel'
        )
    st.markdown("</div>", unsafe_allow_html=True)

# --- Conclusões e Recomendações ---
if not filtered_df.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-title'>CONCLUSÕES E RECOMENDAÇÕES</h3>", unsafe_allow_html=True)
    total_budget = filtered_df['BUDGET'].sum()
    total_realizado = filtered_df['Quantidade_iTRACKER'].sum()
    performance_geral = (total_realizado / total_budget) * 100 if total_budget > 0 else 0
    total_oportunidades = filtered_df['Importação'].sum() + filtered_df['Exportação'].sum() + filtered_df['Cabotagem'].sum()
    aproveitamento_geral = (total_realizado / total_oportunidades) * 100 if total_oportunidades > 0 else 0
    clientes_prioritarios = filtered_df.groupby('Cliente').agg({
        'BUDGET': 'sum',
        'Quantidade_iTRACKER': 'sum'
    })
    clientes_prioritarios['Performance'] = (clientes_prioritarios['Quantidade_iTRACKER'] / clientes_prioritarios['BUDGET']) * 100
    clientes_prioritarios = clientes_prioritarios.sort_values(['BUDGET', 'Performance'])
    clientes_prioritarios = clientes_prioritarios[
        (clientes_prioritarios['BUDGET'] > clientes_prioritarios['BUDGET'].median()) &
        (clientes_prioritarios['Performance'] < 70) &
        (clientes_prioritarios['Performance'] > 0)
    ]
    top_prioritarios = clientes_prioritarios.head(3)
    st.markdown(f"""
    <div style='background-color:{COLORS['background']}; padding:15px; border-radius:8px;'>
        <h4 style='margin-top:0'>📈 ANÁLISE DE PERFORMANCE</h4>
        <p>Com base nos dados analisados, a performance geral está em <b>{format_percent(performance_geral)}</b> do budget projetado, com um aproveitamento de oportunidades de <b>{format_percent(aproveitamento_geral)}</b>.</p>
        <h4>🎯 RECOMENDAÇÕES</h4>
        <ol>
    """, unsafe_allow_html=True)
    if performance_geral < 70:
        st.markdown("""
            <li><b>ATENÇÃO IMEDIATA:</b> A performance geral está abaixo da meta aceitável de 70%. Revisar a estratégia para aumentar os containers movimentados.</li>
        """, unsafe_allow_html=True)
    elif performance_geral < 100:
        st.markdown("""
            <li><b>OPORTUNIDADE DE MELHORIA:</b> A performance está intermediária. Há espaço para otimização das operações comerciais.</li>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <li><b>MANTER ESTRATÉGIA:</b> A performance está atingindo ou superando o budget. Recomenda-se manter a estratégia atual.</li>
        """, unsafe_allow_html=True)
    if aproveitamento_geral < 50:
        st.markdown("""
            <li><b>MELHORAR APROVEITAMENTO:</b> A taxa de aproveitamento está baixa. Reveja os processos de prospecção e conversão.</li>
        """, unsafe_allow_html=True)
    elif aproveitamento_geral < 70:
        st.markdown("""
            <li><b>APRIMORAR CONVERSÃO:</b> A taxa está intermediária. Considere treinamentos e estratégias de follow-up.</li>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <li><b>EXCELENTE APROVEITAMENTO:</b> A taxa está alta. Mantenha os processos e explore novas oportunidades.</li>
        """, unsafe_allow_html=True)
    if not top_prioritarios.empty:
        st.markdown("<h4>CLIENTES PRIORITÁRIOS PARA AÇÕES</h4>", unsafe_allow_html=True)
        st.markdown("<ul>", unsafe_allow_html=True)
        for idx, row in top_prioritarios.iterrows():
            st.markdown(f"<li><b>{idx}</b>: Performance de {row['Performance']:.1f}% com budget de {format_number(row['BUDGET'])}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
    st.markdown("</ol></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown(f"""
<div class="custom-footer">
    <span>📅 ATUALIZADO EM: {current_date}</span> | 
    <span>📧 EMAIL: COMERCIAL@EMPRESA.COM</span> | 
    <span>📞 TELEFONE: (21) 99999-9999</span>
</div>
""", unsafe_allow_html=True)
