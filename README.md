📊 Dashboard Operacional SECAD

Dashboard desenvolvido em Python utilizando Streamlit para monitoramento operacional de vendas e performance de atendimento do Call Center em tempo quase real.

O objetivo do projeto é consolidar dados de vendas, tentativas de contato e atendimentos realizados, permitindo acompanhamento rápido de indicadores operacionais e suporte à tomada de decisão.

🚀 Funcionalidades

O dashboard apresenta indicadores operacionais relevantes para acompanhamento da operação:

📍 Taxa de Localização

Percentual de clientes efetivamente atendidos em relação às tentativas realizadas.
Indicador fundamental para medir eficiência de contato da operação.

📞 Atendimentos por Área

Visualização da performance de atendimento por área de atuação:

Psicologia
Medicina
Pediatria
Nutrição
Fisioterapia
Enfermagem
Veterinária
Outras áreas

Permite identificar onde a operação está conseguindo converter mais contatos.

💰 Vendas por Área

Análise do volume financeiro gerado por cada área de produto.

O gráfico permite:
Comparar performance entre áreas
Identificar áreas com maior geração de receita
Acompanhar variações operacionais ao longo do tempo

📊 Indicadores Monitorados

Principais métricas exibidas no dashboard:
Total de tentativas de contato
Total de atendimentos realizados
Taxa de localização
Volume de vendas
Distribuição de vendas por área
Distribuição de atendimentos por área

🧠 Arquitetura de Dados

O dashboard consolida dados provenientes de dois fluxos principais:
Sistema de Vendas
Base responsável por registrar:
compras realizadas
produtos vendidos
valores das vendas
canal de aquisição
Sistema de Atendimento
Base responsável por registrar:
tentativas de ligação
atendimentos realizados
campanhas ativas
dados de contato dos clientes
Os dados são tratados e agregados utilizando SQL com CTEs, permitindo a construção de métricas operacionais diretamente no banco.

🛠 Tecnologias Utilizadas

Python
Streamlit
Pandas
Plotly
PostgreSQL

Essas ferramentas permitem a criação de um dashboard interativo, leve e rápido, ideal para acompanhamento operacional diário.

⚙️ Como executar o projeto

1️⃣ Clonar o repositório
git clone https://github.com/seu-usuario/dashboard-operacional-secad.git

2️⃣ Instalar dependências
pip install -r requirements.txt

3️⃣ Executar o dashboard
streamlit run monitor_operacional.py

O dashboard será aberto automaticamente no navegador.

📈 Objetivo do Projeto

Este projeto foi desenvolvido com foco em:
Monitoramento operacional
Consolidação de dados de múltiplas fontes
Visualização rápida de indicadores
Apoio à tomada de decisão em operações de vendas e atendimento
A proposta é fornecer visibilidade em tempo quase real da performance operacional.

🔮 Melhorias Futuras

Planejadas para próximas versões do projeto:
Indicadores de conversão por área
Monitoramento horário de vendas
Taxa de atendimento por campanha
Alertas operacionais automáticos
Deploy do dashboard em ambiente cloud

👨‍💻 Autor

Wellington Rodrigues

Projeto desenvolvido como iniciativa de análise de dados aplicada a operações comerciais e atendimento.
