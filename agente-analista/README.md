# 🤖 Agente Analista Administrativo

Projeto didático que demonstra como a Inteligência Artificial pode
**apoiar** tarefas de administração — mantendo o **controle humano**
sobre todas as decisões relevantes.

## Como executar

1. Instale as dependências (recomenda-se criar um ambiente virtual antes):

   ```bash
   pip install -r requirements.txt
   ```

2. Rode o dashboard:

   ```bash
   streamlit run app.py
   ```

3. O navegador abrirá automaticamente em `http://localhost:8501`.
   Se preferir, deixe a caixa "Usar dataset de exemplo" marcada para
   já ver o agente funcionando com a base fictícia da empresa
   `data/dados_empresa.csv`.

## Estrutura do projeto

```
agente-analista/
├── app.py                  # Interface principal (Streamlit) — ponto de entrada
├── agent/
│   ├── analyzer.py          # MÓDULO DE ANÁLISE      — calcula KPIs e gráficos
│   ├── reporter.py           # MÓDULO DE RELATÓRIOS   — gera texto/insights
│   ├── recommender.py        # MÓDULO DE RECOMENDAÇÕES — sugere ações
│   └── validator.py          # MÓDULO DE VALIDAÇÃO HUMANA — checkpoint de decisão
├── data/
│   └── dados_empresa.csv     # Dataset fictício de exemplo (vendas/estoque)
├── utils/
│   └── helpers.py            # Funções auxiliares (formatação, leitura de arquivo)
└── requirements.txt
```

## Ideia central: "IA sugere, humano decide"

O fluxo de informação segue sempre esta ordem:

```
Dados brutos (CSV/Excel)
        │
        ▼
Módulo de Análise      → calcula KPIs (faturamento, ticket médio, giro de estoque)
        │
        ▼
Módulo de Relatórios   → transforma os KPIs em texto e insights automáticos
        │
        ▼
Módulo de Recomendações → sugere ações a partir dos padrões encontrados
        │
        ▼
Módulo de Validação Humana → registra a decisão de uma PESSOA (aprovar,
                              ajustar ou rejeitar) — nada é executado sozinho
```

Na aba **"💡 Recomendações & Validação"** do dashboard, cada sugestão
da IA só se torna uma "decisão" depois que alguém explicitamente
clica em Aprovar, Ajustar ou Rejeitar e informa seu nome como
responsável. Isso é o que chamamos de **human-in-the-loop**
(humano no circuito de decisão) — um princípio central no uso
responsável de IA em contextos administrativos e corporativos.

## Sobre o dataset de exemplo

O arquivo `data/dados_empresa.csv` contém dados **fictícios** de uma
distribuidora de vestuário/calçados/acessórios ao longo de 6 meses
(jan–jun/2025), com colunas de vendas e estoque:

| Coluna | Descrição |
|---|---|
| `data` | Data da venda |
| `produto` | Nome do produto |
| `categoria` | Categoria do produto |
| `vendedor` | Vendedor responsável pela venda |
| `quantidade_vendida` | Quantidade vendida na transação |
| `preco_unitario` | Preço unitário do produto |
| `valor_total` | Valor total da venda (quantidade × preço) |
| `estoque_atual` | Estoque do produto no momento da venda |
| `estoque_minimo` | Estoque mínimo recomendado para o produto |
| `meta_mensal_vendedor` | Meta de referência do vendedor no período |

Você também pode enviar seu próprio arquivo CSV/Excel pela barra
lateral, desde que ele tenha essas mesmas colunas.

## Para os alunos: por que essa arquitetura?

Separar o agente em 4 módulos independentes não é só uma questão de
organização de código — é uma forma de tornar visível, passo a passo,
o que a IA está fazendo em cada etapa: o que ela **observou** (Análise),
o que ela **concluiu** (Relatórios), o que ela **sugere** (Recomendações)
e, por fim, onde a **pessoa responsável** entra para decidir
(Validação Humana). Essa transparência é o que diferencia um "agente
de apoio à decisão" de uma "caixa preta automática".
