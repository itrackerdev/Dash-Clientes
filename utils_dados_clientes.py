import json
import pandas as pd
from datetime import datetime
import unicodedata

def criar_json_dados_clientes(path_excel="comparativo_final_atualizado.xlsx", path_json="dados_clientes_estruturado.json"):
    """
    Lê a planilha Excel atualizada com os dados dos clientes,
    estrutura os dados em um dicionário indexado por Cliente e Mês e
    salva o resultado em formato JSON.
    
    Parâmetros:
        path_excel (str): Caminho para o arquivo Excel com os dados atualizados.
        path_json (str): Caminho para o arquivo JSON a ser gerado.
        
    Retorna:
        dict: Dicionário com os dados dos clientes estruturados.
    """
    try:
        # Tenta ler a primeira aba do arquivo Excel
        xls = pd.ExcelFile(path_excel)
        df = xls.parse(xls.sheet_names[0])
    except Exception as e:
        raise Exception(f"Erro ao carregar a planilha Excel: {e}")
    
    # Normaliza os nomes dos clientes para caixa alta e remove espaços extras
    df['Cliente'] = df['Cliente'].str.upper().str.strip()
    # Converte a coluna "MÊS" para numérico (transformando erros em NaN)
    df['MÊS'] = pd.to_numeric(df['MÊS'], errors='coerce')
    
    # Estrutura os dados em um dicionário: Cliente -> (Mês -> métricas)
    dados_por_cliente = {}
    for _, row in df.iterrows():
        cliente = row['Cliente']
        try:
            mes = int(row['MÊS'])
        except (ValueError, TypeError):
            continue  # Se não conseguir converter o mês, ignora o registro
        if cliente not in dados_por_cliente:
            dados_por_cliente[cliente] = {}
        dados_por_cliente[cliente][str(mes)] = {
            "budget": row['BUDGET'],
            "importacao": row['Importação'],
            "exportacao": row['Exportação'],
            "cabotagem": row['Cabotagem'],
            "quantidade_itracker": row['Quantidade_iTRACKER'],
            "aproveitamento_oportunidade": row['Aproveitamento de Oportunidade (%)'],
            "realizacao_budget": row['Realização do Budget (%)'],
            "desvio_budget_vs_oportunidade": row['Desvio Budget vs Oportunidade (%)'],
            "target_diario_esperado": row['Target Diário Esperado'],
            "target_acumulado": row['Target Acumulado'],
            "gap_realizacao": row['Gap de Realização']
        }
    
    # Salva o dicionário em formato JSON, com indentação para melhor visualização
    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(dados_por_cliente, f, indent=4, ensure_ascii=False)
    
    return dados_por_cliente

def carregar_dados_estruturados(path_excel="comparativo_final_atualizado.xlsx", path_json="dados_clientes_estruturado.json"):
    """
    Atualiza o arquivo JSON com os dados da planilha atualizada e retorna os dados estruturados.
    Essa função garante que, a cada execução, os dados lidos sejam os mais recentes.
    
    Parâmetros:
        path_excel (str): Caminho para o arquivo Excel atualizado.
        path_json (str): Caminho para o arquivo JSON de saída.
        
    Retorna:
        dict: Dados dos clientes estruturados.
    """
    criar_json_dados_clientes(path_excel, path_json)
    with open(path_json, "r", encoding="utf-8") as f:
        return json.load(f)

def normalizar_texto(texto):
    """
    Converte o texto para caixa alta, remove espaços extras e acentuação.
    
    Parâmetros:
        texto (str): Texto a ser normalizado.
        
    Retorna:
        str: Texto normalizado.
    """
    if not isinstance(texto, str):
        return ""
    return unicodedata.normalize('NFKD', texto.strip().upper()).encode('ASCII', 'ignore').decode('ASCII')

def consultar_dados_cliente(dados, cliente, mes=None):
    """
    Consulta os dados de um cliente para um determinado mês e retorna uma resposta formatada com as principais métricas.
    
    Parâmetros:
        dados (dict): Dicionário de dados dos clientes estruturados.
        cliente (str): Nome do cliente a ser consultado.
        mes (int, opcional): Mês para consulta. Se não informado, utiliza o mês atual.
        
    Retorna:
        str: Resposta formatada com os dados do cliente.
    """
    cliente = normalizar_texto(cliente)
    if not mes:
        mes = datetime.now().month
    mes = str(mes)
    
    if cliente not in dados:
        return f"Cliente '{cliente}' não encontrado na base de dados."
    
    if mes not in dados[cliente]:
        return f"Não há dados registrados para o cliente '{cliente}' no mês {mes}."
    
    info = dados[cliente][mes]
    resposta = (
        f"📊 **Análise de {cliente} no mês {mes}:**\n\n"
        f"- 🎯 **BUDGET**: {info['budget']}\n"
        f"- 🚚 **REALIZADO (SYSTRACKER)**: {info['quantidade_itracker']}\n"
        f"- 📦 **OPORTUNIDADES**: {info['importacao']} importações, {info['exportacao']} exportações, {info['cabotagem']} cabotagens\n"
        f"- 📈 **REALIZAÇÃO DO BUDGET**: {info['realizacao_budget']:.1f}%\n"
        f"- ✅ **APROVEITAMENTO DE OPORTUNIDADE**: {info['aproveitamento_oportunidade']:.1f}%\n"
        f"- 🧮 **TARGET ACUMULADO ATÉ HOJE**: {info['target_acumulado']:.1f}\n"
        f"- ⚠️ **GAP DE REALIZAÇÃO**: {info['gap_realizacao']:.1f} containers\n"
    )
    return resposta
