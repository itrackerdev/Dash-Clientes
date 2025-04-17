import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import io, os, math
import base64

# Import dos módulos criados
from data_loader import download_file_from_gdrive, validate_dataframe
from style import COLORS, get_css
from metrics import format_number, format_percent, custom_round

# --- Função para converter PNG em base64 ---
def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# --- Pré‑carrega todos os ícones como base64 ---
ICON_BUDGET      = img_to_base64("assets/budget-icon.png")
ICON_OPORTU      = img_to_base64("assets/oportu-icon.png")
ICON_REALIZADO   = img_to_base64("assets/realizado-icon.png")
ICON_PERFORMANCE = img_to_base64("assets/perf-bud-icon.png")

# Configuração da página
st.set_page_config(
    page_title="Dashboard Comercial - Budget vs Logcomex vs iTracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Seleção de Tema na Sidebar ---
st.markdown(get_css("Clean"), unsafe_allow_html=True)

# Cabeçalho do dashboard
st.markdown("""
    <style>
        .titulo-dashboard-container {
            position: relative;
            padding: 35px 30px;
            border-radius: 15px;
            background: linear-gradient(to right, #F37021, #ffffff);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            text-align: center;
        }
        .titulo-dashboard {
            font-size: 38px;
            font-weight: 800;
            color: #212529;
            margin: 0;
        }
        .subtitulo-dashboard {
            position: absolute;
            bottom: 15px;
            right: 30px;
            font-size: 13px;
            font-style: italic;
            font-weight: 400;
            color: #8A8A8A;
            margin: 0;
        }
        @media (max-width: 768px) {
            .titulo-dashboard { font-size:28px; }
            .subtitulo-dashboard {
                position: static;
                margin-top:10px;
                text-align:center;
                display:block;
            }
            .titulo-dashboard-container { padding-bottom:50px; }
        }
    </style>
    <div class="titulo-dashboard-container">
        <h1 class="titulo-dashboard">DASHBOARD DE ANÁLISE COMERCIAL DE CLIENTES</h1>
        <p class="subtitulo-dashboard">Monitoramento em tempo real do desempenho comercial</p>
    </div>
""", unsafe_allow_html=True)

current_date = datetime.now().strftime("%d de %B de %Y")

# --- Carregamento dos dados ---
df = download_file_from_gdrive()
if df is None:
    st.error("Não foi possível carregar os dados do Google Sheets.")
    st.stop()

df = validate_dataframe(df)
df = df[df['Cliente'].notna() & (df['Cliente'] != "undefined")]
df['Cliente'] = df['Cliente'].str.upper()
numeric_cols = ['MÊS','BUDGET','Importação','Exportação','Cabotagem','Quantidade_iTRACKER']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# --- Sidebar: Filtros ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtros de Análise")
meses_map = {1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",7:"Julho",8:"Agosto",
             9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}
meses_disponiveis = sorted(df['MÊS'].unique())
mes_selecionado = st.sidebar.multiselect(
    "Selecione o(s) mês(es):",
    options=meses_disponiveis,
    format_func=lambda x: meses_map.get(x, x),
    default=[meses_disponiveis[0]] if meses_disponiveis else []
)
clientes_disponiveis = sorted(df['Cliente'].unique())
cliente_selecionado = st.sidebar.multiselect("Selecione o(s) cliente(s):", options=clientes_disponiveis)
if st.sidebar.button("Limpar Filtros"):
    mes_selecionado = []
    cliente_selecionado = []
st.sidebar.markdown("---")
show_detailed_table = st.sidebar.checkbox("Mostrar tabela detalhada", value=True)
chart_height = st.sidebar.slider("Altura dos gráficos", 400, 800, 500, 50)

# Aplica filtros
if mes_selecionado and cliente_selecionado:
    filtered_df = df[df['MÊS'].isin(mes_selecionado) & df['Cliente'].isin(cliente_selecionado)]
elif mes_selecionado:
    filtered_df = df[df['MÊS'].isin(mes_selecionado)]
elif cliente_selecionado:
    filtered_df = df[df['Cliente'].isin(cliente_selecionado)]
else:
    filtered_df = df.copy()

# Mostra filtros ativos
if mes_selecionado or cliente_selecionado:
    filtros = []
    if mes_selecionado:
        meses_txt = [meses_map[m] for m in mes_selecionado]
        filtros.append(f"Meses: {', '.join(meses_txt)}")
    if cliente_selecionado:
        filtros.append(f"Clientes: {', '.join(cliente_selecionado)}")
    st.markdown(f"<div style='background-color:#E3F2FD;padding:10px;border-radius:5px;'>"
                f"<b>Filtros ativos:</b> {' | '.join(filtros)}</div>", unsafe_allow_html=True)

st.divider()

# --- Seção de KPIs com ícones embutidos em Base64 ---
st.markdown(
    "<div class='section' style='text-align: center;'><h3 class='section-title'>📊 VISÃO GERAL</h3></div>",
    unsafe_allow_html=True
)

# Função do KPI
def kpi_card(col, icon_b64, title, value, value_style=""):
    col.markdown(f"""
    <div style="
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: center;
        padding: 18px 24px;
        border-radius: 12px;
        background-color: #f9f9f9;
        border-left: 6px solid #2196F3;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        min-width: 200px;
        max-width: 250px;
        margin: auto;
    ">
        <img src="data:image/png;base64,{icon_b64}" width="34" height="34" style="margin-right:14px;" />
        <div style="display: flex; flex-direction: column; line-height: 1.2;">
            <span style="font-size: 13px; color: #555;">{title}</span>
            <span style="font-size: 22px; font-weight: 700; {value_style}">{value}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Container com mais espaçamento
left, center, right = st.columns([0.5, 10, 0.5])
with center:
    # Espaçamento maior entre KPIs: aumentamos os valores intermediários
    col1, spacer1, col2, spacer2, col3, spacer3, col4 = st.columns([1, 0.5, 1, 0.5, 1, 0.5, 1])

    # KPI 1: TOTAL BUDGET
    total_budget = filtered_df['BUDGET'].sum()
    kpi_card(col1, ICON_BUDGET, "TOTAL BUDGET   ", format_number(total_budget))

    # KPI 2: TOTAL OPORTUNIDADES
    total_oport = (
        filtered_df['Importação'].sum() +
        filtered_df['Exportação'].sum() +
        filtered_df['Cabotagem'].sum()
    )
    kpi_card(col2, ICON_OPORTU, "TOTAL OPORTUNIDADES", format_number(total_oport))

    # KPI 3: REALIZADO
    total_itr = filtered_df['Quantidade_iTRACKER'].sum()
    kpi_card(col3, ICON_REALIZADO, "REALIZADO (SYSTRACKER)", format_number(total_itr))

    # KPI 4: PERFORMANCE
    perf_val = (total_itr / total_budget * 100) if total_budget else 0
    color = "color:red;" if perf_val < 100 else "color:green;"
    kpi_card(col4, ICON_PERFORMANCE, "PERFORMANCE VS BUDGET", format_percent(perf_val), value_style=color)

st.divider()

# --- Tabela de Dados Detalhados ---
if show_detailed_table and not filtered_df.empty:

    # 1) Ordenação inicial 
    detailed_df = filtered_df.sort_values(['Cliente'])
    
    # 2) Seleção e renomeação de colunas (removendo a coluna MÊS)
    detailed_df = detailed_df[[
        'Cliente','BUDGET','Target Acumulado',
        'Quantidade_iTRACKER','Gap de Realização',
        'Importação','Exportação','Cabotagem'
    ]]
    detailed_df.columns = [
        'CLIENTE','BUDGET (MENSAL)','TARGET ACUMULADO',
        'REALIZADO (SYSTRACKER)','GAP DE REALIZAÇÃO',
        'OP. IMPO','OP. EXPO','OP. CABO.'
    ]

    # 3) Arredondar e converter para int
    numeric_cols = [
        'BUDGET (MENSAL)','TARGET ACUMULADO','REALIZADO (SYSTRACKER)',
        'GAP DE REALIZAÇÃO','OP. IMPO','OP. EXPO','OP. CABO.'
    ]
    for col in numeric_cols:
        detailed_df[col] = detailed_df[col].round(0).astype(int)

    # 4) Preparar opções e estados
    clientes = sorted(detailed_df['CLIENTE'].unique().tolist())
    sort_options = ["CLIENTE","BUDGET (MENSAL)","REALIZADO (SYSTRACKER)","GAP DE REALIZAÇÃO"]
    selected = st.session_state.get("selected_client", "Todos")
    sort_by = st.session_state.get("sort_by", "CLIENTE")
    records_per_page = st.session_state.get("records_per_page", 10)
    page = st.session_state.get("detailed_table_page", 1)

    # Exibir título
    st.markdown(
        "<div class='section' style='text-align: center;'><h3 class='section-title'>📊 DADOS REFERENTES AO MÊS DE ABRIL</h3></div>",
        unsafe_allow_html=True
    )

    # 5) Controles de filtro e ordenação
    with st.container():
        filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1], gap="medium")
        with filter_col1:
            selected = st.selectbox(
                "Selecionar Cliente",
                ["Todos"] + clientes,
                index=(["Todos"]+clientes).index(selected),
                key="selected_client"
            )
        with filter_col2:
            sort_by = st.selectbox(
                "Ordenar Por",
                sort_options,
                index=sort_options.index(sort_by),
                key="sort_by"
            )
        with filter_col3:
            records_per_page = st.selectbox(
                "Registros por página",
                [10, 25, 50, 100],
                index=[10, 25, 50, 100].index(records_per_page),
                key="records_per_page"
            )

    # 6) Filtrar e ordenar
    df_filt = detailed_df.copy()
    if selected != "Todos":
        df_filt = df_filt[df_filt['CLIENTE']==selected]
    if sort_by == "CLIENTE":
        df_filt = df_filt.sort_values(['CLIENTE'])
    else:
        df_filt = df_filt.sort_values(sort_by, ascending=False)

    # 7) Paginar
    total_pages = max(1, (len(df_filt)-1)//records_per_page + 1)
    page = min(page, total_pages)
    start = (page-1)*records_per_page
    end = start + records_per_page
    paginated_df = df_filt.iloc[start:end].reset_index(drop=True)
    st.session_state["detailed_table_page"] = page

    # 8) Renderizar tabela HTML com cores por célula da coluna GAP
    styles = """
    <style>
    table.custom-table { width:100%; border-collapse:collapse; font-size:14px; margin-bottom: 20px; }
    .custom-table th { background:#f1f3f5; padding:8px; text-align:center; }
    .custom-table td { padding:8px; }
    .text-left { text-align:left; }
    .text-center { text-align:center; }
    .op-column { background-color: rgba(255, 255, 0, 0.1); }
    </style>
    """
    html = styles + "<table class='custom-table'><thead><tr>"
    for col in paginated_df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for _, row in paginated_df.iterrows():
        html += "<tr>"
        for col in paginated_df.columns:
            align = "text-center" if col in numeric_cols else "text-left"
            cell_style = ""
            if col == "GAP DE REALIZAÇÃO":
                value = row[col]
                if value > 0:
                    cell_style = "background-color: rgba(255, 0, 0, 0.1);"
                elif value < 0:
                    cell_style = "background-color: rgba(0, 128, 0, 0.15);"
            elif col in ["OP. IMPO", "OP. EXPO", "OP. CABO."]:
                cell_style = "background-color: rgba(255, 255, 0, 0.1);"
            html += f"<td class='{align}' style='{cell_style}'>{row[col]}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

    # 9) Rodapé com navegação e downloads organizados
    nav_styles = """
    <style>
    .nav-btn {
        font-size: 20px;
        color: #444;
        background-color: transparent;
        border: 1px solid #ccc;
        cursor: pointer;
        padding: 6px 12px;
        border-radius: 6px;
        transition: background-color 0.2s ease;
    }
    .nav-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }
    </style>
    """
    st.markdown(nav_styles, unsafe_allow_html=True)

    col_nav1, col_nav2, col_center, col_dl1, col_dl2 = st.columns([1, 1, 6, 1, 1])

    with col_nav1:
        st.button("◀", key="prev_page_btn", disabled=(page <= 1), help="Página anterior")
    with col_nav2:
        st.button("▶", key="next_page_btn", disabled=(page >= total_pages), help="Próxima página")

    if "prev_page_btn" in st.session_state and st.session_state["prev_page_btn"] and page > 1:
        st.session_state["detailed_table_page"] = page - 1
    if "next_page_btn" in st.session_state and st.session_state["next_page_btn"] and page < total_pages:
        st.session_state["detailed_table_page"] = page + 1

    with col_dl1:
        st.download_button(
            "📥 BAIXAR CSV",
            df_filt.to_csv(index=False),
            "dados_detalhados.csv",
            "text/csv",
            key="download-csv"
        )
    with col_dl2:
        buf = io.BytesIO()
        df_filt.to_excel(buf, index=False, engine='openpyxl')
        excel_data = buf.getvalue()
        st.download_button(
            "📥 BAIXAR EXCEL",
            excel_data,
            "dados_detalhados.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download-excel"
        )

st.divider()

# --- Gráfico 1: Performance vs Budget ---
if not filtered_df.empty:
    budget_df = filtered_df[filtered_df['BUDGET'] > 0].copy()
    if not budget_df.empty:
        st.markdown(
            "<div class='section' style='text-align: center;'><h3 class='section-title'>📊 PERFORMANCE VS BUDGET POR CLIENTE</h3></div>",
            unsafe_allow_html=True
        )


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
        
        # --- INSIGHTS DO GRÁFICO DE PERFORMANCE ---
        total_clientes = len(df_graph3)
        clientes_acima_meta = len(df_graph3[df_graph3['Performance'] >= 100])
        clientes_atencao = len(df_graph3[(df_graph3['Performance'] < 100) & (df_graph3['Performance'] >= 70)])
        clientes_critico = len(df_graph3[df_graph3['Performance'] < 70])
        data_atual = datetime.now().strftime('%d de %B')

        st.markdown(f"""
        <div style='background-color:{COLORS['background']}; padding:10px; border-radius:5px; margin-top:10px;'>
            <h5 style='margin-top:0'>📊 INSIGHTS - PERFORMANCE</h5>
            <p style='margin-bottom:10px;'>Com base nos dados disponíveis até o dia <b>{data_atual}</b>, dos {total_clientes} clientes analisados:</p>
            <ul>
                <li><span style='color:{COLORS["success"]};'>✓ {clientes_acima_meta} clientes ({clientes_acima_meta/total_clientes*100:.1f}%) atingem ou superam a meta</span></li>
                <li><span style='color:{COLORS["warning"]};'>⚠️ {clientes_atencao} clientes ({clientes_atencao/total_clientes*100:.1f}%) estão em zona de atenção (70-99%)</span></li>
                <li><span style='color:{COLORS["danger"]};'>❌ {clientes_critico} clientes ({clientes_critico/total_clientes*100:.1f}%) estão em situação crítica (<70%)</span></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("SEM DADOS DE BUDGET DISPONÍVEIS PARA OS FILTROS SELECIONADOS.")
st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- Gráfico 2: GAP de Atendimento ---
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

        st.markdown(
            "<div class='section' style='text-align: center;'><h3 class='section-title'>🚨 CLIENTES COM MAIOR GAP VS TARGET ACUMULADO</h3></div>",
            unsafe_allow_html=True
        )

        st.plotly_chart(fig_gap, use_container_width=True)

        # --- INSIGHTS DO GRÁFICO DE GAP ---
        total_gap = df_gap['Gap de Realização'].sum()
        media_gap = df_gap['Gap de Realização'].mean()
        top_cliente_gap = df_gap.iloc[0]['Cliente']
        top_gap_valor = df_gap.iloc[0]['Gap de Realização']
        data_atual = datetime.now().strftime('%d de %B')

        st.markdown(f"""
        <div style='background-color:{COLORS['background']}; padding:10px; border-radius:5px; margin-top:10px;'>
            <h5 style='margin-top:0'>📊 INSIGHTS - GAP DE ATENDIMENTO</h5>
            <p style='margin-bottom:10px;'>Com base nos dados disponíveis até o dia <b>{data_atual}</b>, os principais destaques são:</p>
            <ul>
                <li>O GAP TOTAL no mês corrente é de <b>{format_number(total_gap)}</b> containers</li>
                <li>A MÉDIA de gap entre os clientes é de <b>{format_number(media_gap)}</b> containers</li>
                <li>O MAIOR GAP é do cliente <b>{top_cliente_gap}</b> com <b>{format_number(top_gap_valor)}</b> containers</li>
                <li>{"Mais da metade dos clientes apresentam GAP acima da média" if (df_gap['Gap de Realização'] > media_gap).mean() > 0.5 else "A maioria dos clientes está abaixo da média de GAP"}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

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

st.divider()

# --- Gráfico 3: Comparativo Budget vs Realizado por Categoria ---
if not filtered_df.empty:
    st.markdown(
        "<div class='section' style='text-align: center;'><h3 class='section-title'>📊 COMPARATIVO BUDGET VS REALIZADO POR CATEGORIA</h3></div>",
        unsafe_allow_html=True
    )


    # Utilizar os mesmos dados filtrados usados nos KPIs
    df_mes_atual = filtered_df.copy()

    # Agregar os dados para todos os clientes (para os insights completos)
    df_grouped_all = df_mes_atual.groupby('Cliente', as_index=False).agg({
        'BUDGET': 'sum',
        'Importação': 'sum',
        'Exportação': 'sum',
        'Cabotagem': 'sum',
        'Quantidade_iTRACKER': 'sum'
    })
    df_grouped_all = df_grouped_all.rename(columns={
        'Quantidade_iTRACKER': 'Realizado (Systracker)'
    })

    df_grouped_all['Total'] = df_grouped_all[[
        'BUDGET', 'Importação', 'Exportação', 'Cabotagem', 'Realizado (Systracker)'
    ]].sum(axis=1)

    # Para o gráfico, limitar a visualização aos 15 clientes com maior movimentação (baseado em Total)
    df_grouped = df_grouped_all.sort_values('Total', ascending=False).head(15)

    # Derreter (melt) para o gráfico
    df_melted = df_grouped.melt(
        id_vars='Cliente',
        value_vars=[
            'BUDGET', 'Importação', 'Exportação', 'Cabotagem', 'Realizado (Systracker)'
        ],
        var_name='Categoria',
        value_name='Quantidade'
    )
    df_melted = df_melted[df_melted['Quantidade'] > 0]
    df_melted['Categoria_Label'] = df_melted['Categoria']

    # Criar gráfico com nova categoria
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
            'Cabotagem': '#FFB300',
            'Realizado (Systracker)': '#6A1B9A'  # Roxo para a nova barra
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

    # --- INSIGHTS DO GRÁFICO DE COMPARATIVO ---
    total_budget_all = df_grouped_all['BUDGET'].sum()
    total_importacao = df_grouped_all['Importação'].sum()
    total_exportacao = df_grouped_all['Exportação'].sum()
    total_cabotagem = df_grouped_all['Cabotagem'].sum()
    total_realizado_systracker = df_grouped_all['Realizado (Systracker)'].sum()
    total_realizado = total_importacao + total_exportacao + total_cabotagem

    overall_ratio = (total_realizado / total_budget_all * 100) if total_budget_all > 0 else 0
    realized_categories = {
        'Importação': total_importacao,
        'Exportação': total_exportacao,
        'Cabotagem': total_cabotagem,
        'Realizado (Systracker)': total_realizado_systracker
    }
    top_category = max(realized_categories, key=realized_categories.get)
    data_atual = datetime.now().strftime('%d de %B')

    st.markdown(f"""
    <div style='background-color:{COLORS['background']}; padding:10px; border-radius:5px; margin-top:10px;'>
        <h5 style='margin-top:0'>📊 INSIGHTS - COMPARATIVO BUDGET VS REALIZADO</h5>
        <p style='margin-bottom:10px;'>Com base nos dados disponíveis até o dia <b>{data_atual}</b> (somente mês corrente):</p>
        <ul>
            <li>Budget total previsto: <b>{format_number(total_budget_all)}</b> containers</li>
            <li>Total de containers realizados (operacional): <b>{format_number(total_realizado)}</b></li>
            <li>Total de containers registrados (Systracker): <b>{format_number(total_realizado_systracker)}</b></li>
            <li>Categoria com maior movimentação: <b>{top_category}</b> com <b>{format_number(realized_categories[top_category])}</b> containers</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("VER RAZÃO DO CÁLCULO DESTE GRÁFICO"):
        st.markdown("""
        **DETALHAMENTO DO CÁLCULO:**
        - **FILTRAGEM:** Usa os mesmos filtros ativos aplicados no dashboard (mês/cliente).
        - **AGRUPAMENTO:** Dados agrupados por CLIENTE com soma de BUDGET, IMPORTAÇÃO, EXPORTAÇÃO, CABOTAGEM e SYSTRACKER.
        - **TOTAL:** Soma de todas as categorias, incluindo realizado por sistema.
        - Compara o BUDGET com o realizado (campo Systracker + operacional).
        """)

else:
    st.info("SEM DADOS DISPONÍVEIS PARA O GRÁFICO DE COMPARATIVO APÓS APLICAÇÃO DOS FILTROS.")

st.divider()

# --- Gráfico 4: Aproveitamento de Oportunidades por Cliente ---
if not filtered_df.empty:
    opp_df = filtered_df[(filtered_df['Importação']+filtered_df['Exportação']+filtered_df['Cabotagem']) > 0].copy()
    if not opp_df.empty:
        st.markdown(
            "<div class='section' style='text-align: center;'><h3 class='section-title'>📊 APROVEITAMENTO DE OPORTUNIDADES POR CLIENTE</h3></div>",
            unsafe_allow_html=True
        )

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

st.divider()

# ---  Gráfico 5: CLIENTES FORA DO BUDGET COM OPERAÇÕES REALIZADAS --- 
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
    )
    fig_no_budget.update_layout(
        height=chart_height,
        yaxis=dict(autorange="reversed"),
        margin=dict(l=60, r=30, t=40, b=60),
        plot_bgcolor="white"
    )
    fig_no_budget.update_traces(texttemplate='%{text}', textposition='outside')

    st.markdown(
        "<div class='section' style='text-align: center;'><h3 class='section-title'>📊 CLIENTES FORA DO BUDGET COM OPERAÇÕES REALIZADAS</h3></div>",
        unsafe_allow_html=True
    )


    st.plotly_chart(fig_no_budget, use_container_width=True)

    # --- INSIGHTS DO GRÁFICO 3 ---
    total_clientes_sem_budget = df_graph['Cliente'].nunique()
    media_realizados = df_graph['Quantidade_iTRACKER'].mean()
    top_cliente = df_graph.iloc[0]['Cliente']
    top_valor = df_graph.iloc[0]['Quantidade_iTRACKER']
    acima_da_media = (df_graph['Quantidade_iTRACKER'] > media_realizados).mean()
    data_atual = datetime.now().strftime('%d de %B')

    st.markdown(f"""
    <div style='background-color:{COLORS['background']}; padding:10px; border-radius:5px; margin-top:10px;'>
        <h5 style='margin-top:0'>📊 INSIGHTS - CLIENTES FORA DO BUDGET</h5>
        <p style='margin-bottom:10px;'>Com base nas movimentações registradas até <b>{data_atual}</b>, destacamos:</p>
        <ul>
            <li><b>{total_clientes_sem_budget}</b> clientes realizaram operações sem orçamento previsto</li>
            <li>A MÉDIA de containers movimentados por esses clientes é <b>{format_number(media_realizados)}</b></li>
            <li>O cliente com maior volume é <b>{top_cliente}</b>, com <b>{format_number(top_valor)}</b> containers</li>
            <li>{'Mais da metade dos clientes movimentaram acima da média' if acima_da_media > 0.5 else 'A maioria dos clientes movimentou abaixo da média'}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- Conclusões e Recomendações ---
if not filtered_df.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section' style='text-align: center;'><h3 class='section-title'>🧠 CONCLUSÕES E RECOMENDAÇÕES iTracker HUB IA</h3></div>",
        unsafe_allow_html=True
    )



    
    # Indicadores gerais
    total_budget = filtered_df['BUDGET'].sum()
    total_realizado = filtered_df['Quantidade_iTRACKER'].sum()
    performance_geral = (total_realizado / total_budget) * 100 if total_budget > 0 else 0
    total_oportunidades = (filtered_df['Importação'].sum() +
                           filtered_df['Exportação'].sum() +
                           filtered_df['Cabotagem'].sum())
    aproveitamento_geral = (total_realizado / total_oportunidades) * 100 if total_oportunidades > 0 else 0
    data_atual = datetime.now().strftime('%d de %B')
    
    # Resumo e concentração de resultados
    total_registros = filtered_df.shape[0]
    top_clientes = filtered_df.groupby('Cliente')['Quantidade_iTRACKER'].sum().sort_values(ascending=False).head(5)
    percent_top5 = (top_clientes.sum() / total_realizado) * 100 if total_realizado > 0 else 0

    # Clientes prioritários para ações
    clientes_prioritarios = filtered_df.groupby('Cliente').agg({
        'BUDGET': 'sum',
        'Quantidade_iTRACKER': 'sum'
    })
    clientes_prioritarios['Performance'] = (clientes_prioritarios['Quantidade_iTRACKER'] /
                                             clientes_prioritarios['BUDGET']) * 100
    clientes_prioritarios = clientes_prioritarios.sort_values(['BUDGET', 'Performance'])
    clientes_prioritarios = clientes_prioritarios[
        (clientes_prioritarios['BUDGET'] > clientes_prioritarios['BUDGET'].median()) &
        (clientes_prioritarios['Performance'] < 70) &
        (clientes_prioritarios['Performance'] > 0)
    ]
    top_prioritarios = clientes_prioritarios.head(3)

    # Análise por categoria
    importacao = filtered_df['Importação'].sum()
    exportacao = filtered_df['Exportação'].sum()
    cabotagem = filtered_df['Cabotagem'].sum()
    top_categoria = max(
        {'Importação': importacao, 'Exportação': exportacao, 'Cabotagem': cabotagem},
        key=lambda k: {'Importação': importacao, 'Exportação': exportacao, 'Cabotagem': cabotagem}[k]
    )

    # Clientes operando sem budget
    operando_sem_budget = filtered_df[
        ((filtered_df['BUDGET'] == 0) | (filtered_df['BUDGET'].isna())) &
        (filtered_df['Quantidade_iTRACKER'] > 0)
    ]['Cliente'].nunique()

    st.markdown(f"""
    <div style='background-color:{COLORS['background']}; padding:15px; border-radius:8px;'>
        <h4 style='margin-top:0'>📈 ANÁLISE DE PERFORMANCE E CONCLUSÕES</h4>
        <p>Com base nos dados disponíveis até <b>{data_atual.upper()}</b> ({total_registros} registros filtrados):</p>
        <ul>
            <li><b>Performance geral:</b> {format_percent(performance_geral)} do budget projetado.</li>
            <li><b>Aproveitamento total:</b> {format_percent(aproveitamento_geral)} das oportunidades geradas.</li>
            <li><b>Concentração:</b> Top 5 clientes representam {percent_top5:.1f}% do total realizado.</li>
            <li><b>Categoria mais ativa:</b> {top_categoria} com {format_number({'importação': importacao, 'exportação': exportacao, 'cabotagem': cabotagem}[top_categoria.lower()])} containers.</li>
            <li><b>Clientes sem orçamento:</b> {operando_sem_budget} cliente(s) estão operando sem budget definido.</li>
        </ul>
        <h4>🎯 RECOMENDAÇÕES E AÇÕES</h4>
        <ol>
    """, unsafe_allow_html=True)
    
    # Recomendações baseadas na performance
    if performance_geral < 70:
        st.markdown("<li><b>ALERTA:</b> A performance geral está abaixo da meta (abaixo de 70%). Reavaliar estratégias e reforçar o relacionamento com clientes.</li>", unsafe_allow_html=True)
    elif performance_geral < 100:
        st.markdown("<li><b>ATENÇÃO:</b> A performance está em um patamar intermediário. Buscar oportunidades de alavancagem e otimização das operações.</li>", unsafe_allow_html=True)
    else:
        st.markdown("<li><b>RESULTADO POSITIVO:</b> A performance está atingindo ou superando o budget. Manter as estratégias vigentes.</li>", unsafe_allow_html=True)
    
    if aproveitamento_geral < 50:
        st.markdown("<li><b>MELHORAR A CONVERSÃO:</b> O aproveitamento está baixo. Investir em treinamentos e revisar o processo de conversão de oportunidades.</li>", unsafe_allow_html=True)
    elif aproveitamento_geral < 70:
        st.markdown("<li><b>OTIMIZAÇÃO:</b> Aproveitamento razoável. Monitorar e buscar melhorias pontuais nos processos.</li>", unsafe_allow_html=True)
    else:
        st.markdown("<li><b>PROCESSOS EFICIENTES:</b> O aproveitamento é elevado. Explorar novas oportunidades e consolidar as estratégias atuais.</li>", unsafe_allow_html=True)
    
    if not top_prioritarios.empty:
        st.markdown("<li><b>FOCO EM CLIENTES PRIORITÁRIOS:</b> As seguintes empresas apresentaram performance abaixo da meta e merecem ações corretivas:</li>", unsafe_allow_html=True)
        st.markdown("<ul>", unsafe_allow_html=True)
        for idx, row in top_prioritarios.iterrows():
            st.markdown(f"<li><b>{idx}</b>: Performance de {row['Performance']:.1f}% com budget de {format_number(row['BUDGET'])}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
    
    st.markdown("</ol></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- Footer ---
st.markdown(f"""
<div class="custom-footer">
    <span>📅 ATUALIZADO EM: {current_date}</span> | 
    <span>📧 EMAIL: COMERCIAL@EMPRESA.COM</span> | 
    <span>📞 TELEFONE: (21) 99999-9999</span>
</div>
""", unsafe_allow_html=True)
