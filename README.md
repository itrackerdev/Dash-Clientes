
# 📊 Dashboard Comercial - Budget vs Logcomex vs iTracker

Este projeto é um **dashboard interativo desenvolvido em Streamlit** para análise comercial de clientes, com foco em comparar o budget projetado, oportunidades mapeadas na Logcomex e movimentações reais extraídas do sistema iTracker. Ele permite acompanhar em tempo real a performance dos clientes, identificar gaps e extrair insights estratégicos.

---

## 🚀 Funcionalidades

- 📅 Filtros por mês e cliente
- 🎯 Indicadores de desempenho (KPIs)
- 📉 Gráficos interativos com Plotly:
  - GAP de atendimento
  - Performance vs Budget
  - Aproveitamento de oportunidades
  - Comparativo por categoria (Importação, Exportação, Cabotagem)
- 📥 Exportação de dados em Excel e CSV
- 📋 Tabela detalhada com ordenação e busca
- 🧠 Recomendações automatizadas com base nos resultados

---

## 🛠 Tecnologias Utilizadas

- [Python](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [Plotly](https://plotly.com/python/)
- [Google Drive API](https://developers.google.com/drive)
- [OpenPyXL](https://openpyxl.readthedocs.io/en/stable/) (para exportação em Excel)

---

## 📁 Estrutura do Projeto

```
.
├── app.py                         # Arquivo principal com o dashboard
├── data_loader.py                # Módulo para download e validação dos dados
├── metrics.py                    # Funções para formatar indicadores e cálculos personalizados
├── style.py                      # Estilo visual do dashboard (cores e temas)
├── requirements.txt              # Bibliotecas necessárias para execução
└── README.md                     # Documentação do projeto
```

---

## 📦 Instalação e Execução

1. **Clone o repositório:**

```bash
git clone https://github.com/LeonardoRFragoso/dash-clientes.git
cd dash-clientes
```

2. **Crie e ative um ambiente virtual:**

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

3. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

4. **Configure as credenciais de acesso ao Google Drive**:
   - Adicione seu `secrets.toml` na pasta `.streamlit/` com sua chave de serviço:

```toml
[google]
type = "service_account"
project_id = "seu_projeto"
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
```

5. **Execute a aplicação:**

```bash
streamlit run app.py
```

---

## 📊 Exemplos de Uso

- Filtrar por cliente e mês para visualizar KPIs específicos
- Identificar os clientes com maior GAP de atendimento
- Avaliar se a performance geral está abaixo da meta
- Exportar relatórios detalhados para reuniões ou acompanhamento

---

## 📝 Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
