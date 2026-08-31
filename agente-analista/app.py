# -*- coding: utf-8 -*-
"""
app.py
=======

INTERFACE PRINCIPAL DO AGENTE ANALISTA ADMINISTRATIVO
--------------------------------------------------------
Este arquivo é o "ponto de entrada" da aplicação: é ele que você
executa com o comando:

    streamlit run app.py

O Streamlit é uma biblioteca Python que transforma um script comum em
uma aplicação web interativa, sem precisar escrever HTML/CSS/JavaScript.
Cada vez que o usuário interage com algum elemento (um botão, um
upload de arquivo, um filtro), o Streamlit executa este script de novo
de cima para baixo — por isso usamos o `st.session_state` para
"lembrar" informações entre uma execução e outra (como o histórico de
decisões humanas).

ESTRUTURA DESTE ARQUIVO
------------------------
1. Configuração da página e carregamento dos dados
2. Barra lateral (filtros e navegação)
3. Aba "Dashboard de KPIs" -> usa agent/analyzer.py
4. Aba "Relatório Executivo" -> usa agent/reporter.py
5. Aba "Recomendações e Validação" -> usa agent/recommender.py + agent/validator.py
6. Aba "Assistente Administrativo" -> tarefas rotineiras simples

Em cada seção, deixamos comentários "didáticos" (📘) explicando o
raciocínio para quem está estudando Administração e ainda não tem
familiaridade com programação.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from agent.analyzer import AnalisadorDados
from agent.reporter import GeradorRelatorios
from agent.recommender import RecomendadorIA
from agent.validator import ValidadorHumano
from utils.helpers import formatar_moeda, carregar_dados, validar_colunas_necessarias, exibir_tabela


# ============================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Agente Analista Administrativo",
    page_icon="🤖",
    layout="wide",
)

# 📘 O st.session_state funciona como uma "memória" da aplicação
# durante a sessão do usuário. Aqui inicializamos a lista onde vamos
# guardar as decisões humanas tomadas sobre as recomendações da IA.
if "historico_decisoes" not in st.session_state:
    st.session_state.historico_decisoes = []

COLUNAS_NECESSARIAS = [
    "data", "produto", "categoria", "vendedor",
    "quantidade_vendida", "preco_unitario", "valor_total",
    "estoque_atual", "estoque_minimo", "meta_mensal_vendedor",
]


# ============================================================
# CABEÇALHO
# ============================================================
st.title("🤖 Agente Analista Administrativo")
st.caption(
    "Um exemplo didático de como a Inteligência Artificial pode apoiar "
    "tarefas de administração — sempre com o humano no controle da decisão final."
)

with st.expander("ℹ️ Como funciona este agente? (clique para entender a arquitetura)"):
    st.markdown("""
    Este agente é dividido em **4 módulos**, cada um com uma responsabilidade clara:

    | Módulo | Pergunta que responde | Arquivo |
    |---|---|---|
    | 🔎 **Análise** | *O que os dados mostram?* | `agent/analyzer.py` |
    | 📄 **Relatórios** | *Como resumir isso para a diretoria?* | `agent/reporter.py` |
    | 💡 **Recomendações** | *O que poderia ser feito a respeito?* | `agent/recommender.py` |
    | ✅ **Validação Humana** | *O humano aprova, ajusta ou rejeita?* | `agent/validator.py` |

    A IA cuida das três primeiras etapas (analisar, relatar, sugerir).
    A **decisão final é sempre humana** — é isso que o Módulo de
    Validação Humana torna explícito e registrado.
    """)


# ============================================================
# 2. CARREGAMENTO DOS DADOS (barra lateral)
# ============================================================
st.sidebar.header("📂 Dados")
usar_dados_exemplo = st.sidebar.checkbox("Usar dataset de exemplo (empresa fictícia)", value=True)

df = None

if usar_dados_exemplo:
    df = carregar_dados("data/dados_empresa.csv")
    st.sidebar.success("Usando dados fictícios de exemplo.")
else:
    arquivo_enviado = st.sidebar.file_uploader(
        "Envie um arquivo CSV ou Excel com seus dados de vendas/estoque",
        type=["csv", "xlsx", "xls"],
    )
    if arquivo_enviado is not None:
        df = carregar_dados(arquivo_enviado)

if df is None:
    st.warning("⬅️ Selecione o dataset de exemplo ou envie um arquivo na barra lateral para começar.")
    st.stop()

# 📘 Antes de qualquer análise, o agente valida se a base tem as
# colunas mínimas necessárias. Isso evita erros e conclusões erradas
# a partir de dados incompletos — um cuidado importante em qualquer
# projeto real de análise de dados.
valido, colunas_faltando = validar_colunas_necessarias(df, COLUNAS_NECESSARIAS)
if not valido:
    st.error(
        f"O arquivo enviado não possui as colunas necessárias: {', '.join(colunas_faltando)}. "
        f"Colunas esperadas: {', '.join(COLUNAS_NECESSARIAS)}"
    )
    st.stop()

# --- Filtro de período na barra lateral ---
st.sidebar.header("🗓️ Filtro de período")
data_min, data_max = df["data"].min(), df["data"].max()
periodo = st.sidebar.date_input(
    "Selecione o período",
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max,
)
if len(periodo) == 2:
    inicio, fim = periodo
    df = df[(df["data"] >= pd.Timestamp(inicio)) & (df["data"] <= pd.Timestamp(fim))]

if df.empty:
    st.warning("Não há dados para o período selecionado.")
    st.stop()

# ============================================================
# INSTANCIANDO OS MÓDULOS DO AGENTE
# ============================================================
# 📘 Aqui é onde os 4 módulos "ganham vida": criamos um objeto de
# cada classe, passando os dados já filtrados. A partir daqui, cada
# aba do dashboard vai chamar métodos desses objetos.
analisador = AnalisadorDados(df)
relator = GeradorRelatorios(df, analisador)
recomendador = RecomendadorIA(df, analisador)
validador = ValidadorHumano(st.session_state.historico_decisoes)


# ============================================================
# ABAS DO DASHBOARD
# ============================================================
aba_kpis, aba_relatorio, aba_recomendacoes, aba_assistente = st.tabs([
    "📊 Dashboard de KPIs",
    "📄 Relatório Executivo",
    "💡 Recomendações & Validação",
    "🗂️ Assistente Administrativo",
])


# ------------------------------------------------------------------
# ABA 1 — DASHBOARD DE KPIs  (usa agent/analyzer.py)
# ------------------------------------------------------------------
with aba_kpis:
    st.subheader("🔎 O que a IA analisou")
    st.caption(
        "Esta seção mostra os indicadores calculados diretamente a partir "
        "dos dados carregados — sem nenhuma interpretação subjetiva."
    )

    faturamento_total = analisador.calcular_faturamento_total()
    ticket_medio = analisador.calcular_ticket_medio()
    giro = analisador.calcular_giro_estoque()
    giro_medio = giro["giro_estoque"].mean() if not giro.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Faturamento Total", formatar_moeda(faturamento_total))
    col2.metric("🧾 Ticket Médio", formatar_moeda(ticket_medio))
    col3.metric("📦 Giro Médio de Estoque", f"{giro_medio:.2f}x")
    col4.metric("🛒 Nº de Vendas", f"{len(df)}")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(analisador.grafico_faturamento_periodo("ME"), use_container_width=True)
        st.plotly_chart(analisador.grafico_giro_estoque(), use_container_width=True)
    with col_b:
        st.plotly_chart(analisador.grafico_faturamento_categoria(), use_container_width=True)
        st.plotly_chart(analisador.grafico_desempenho_vendedores(), use_container_width=True)

    st.divider()
    st.subheader("🚨 Alertas Inteligentes")
    st.caption("Gerados automaticamente comparando os dados atuais com limites de referência (estoque mínimo e metas).")

    estoque_baixo = analisador.produtos_estoque_baixo()
    vendedores = analisador.faturamento_por_vendedor()
    abaixo_meta = vendedores[vendedores["faturamento"] < vendedores["meta_mensal"]]

    col_alerta1, col_alerta2 = st.columns(2)
    with col_alerta1:
        if len(estoque_baixo) > 0:
            st.error(f"📦 {len(estoque_baixo)} produto(s) com estoque no limite ou abaixo do mínimo:")
            exibir_tabela(estoque_baixo)
        else:
            st.success("✅ Nenhum produto com estoque abaixo do mínimo.")
    with col_alerta2:
        if len(abaixo_meta) > 0:
            st.error(f"🎯 {len(abaixo_meta)} vendedor(es) abaixo da meta acumulada:")
            exibir_tabela(abaixo_meta)
        else:
            st.success("✅ Todos os vendedores estão dentro ou acima da meta.")


# ------------------------------------------------------------------
# ABA 2 — RELATÓRIO EXECUTIVO  (usa agent/reporter.py)
# ------------------------------------------------------------------
with aba_relatorio:
    st.subheader("📄 Relatório Executivo Automático")
    st.caption(
        "Texto gerado a partir de regras de negócio aplicadas sobre os KPIs — "
        "pronto para ser copiado em um e-mail ou apresentação, mas que deve "
        "sempre passar por uma revisão humana antes de ser enviado oficialmente."
    )

    resumo = relator.gerar_resumo_executivo()

    st.markdown(f"**Período analisado:** {resumo['periodo']}")
    st.info(resumo["texto_introducao"])
    st.info(resumo["texto_destaques"])

    st.divider()
    st.subheader("💡 Insights Automáticos")
    st.caption("Cada insight é gerado comparando indicadores atuais com períodos anteriores ou metas de referência.")

    insights = relator.gerar_insights_automaticos()
    icones = {"positivo": "🟢", "atencao": "🟡", "critico": "🔴"}

    if not insights:
        st.write("Nenhum insight relevante identificado para o período selecionado.")
    for insight in insights:
        icone = icones.get(insight["tipo"], "⚪")
        with st.container(border=True):
            st.markdown(f"{icone} **{insight['titulo']}**")
            st.write(insight["descricao"])

    st.divider()
    st.download_button(
        label="⬇️ Baixar relatório em texto (.txt)",
        data=(
            f"RELATÓRIO EXECUTIVO - {resumo['periodo']}\n\n"
            f"{resumo['texto_introducao']}\n\n{resumo['texto_destaques']}\n\n"
            "INSIGHTS:\n" + "\n".join([f"- {i['titulo']}: {i['descricao']}" for i in insights])
        ),
        file_name=f"relatorio_executivo_{datetime.now().strftime('%Y%m%d')}.txt",
    )


# ------------------------------------------------------------------
# ABA 3 — RECOMENDAÇÕES & VALIDAÇÃO HUMANA
#          (usa agent/recommender.py + agent/validator.py)
# ------------------------------------------------------------------
with aba_recomendacoes:
    st.subheader("💡 Sugestões da IA")
    st.caption(
        "⚠️ Estas são SUGESTÕES baseadas em padrões nos dados. "
        "Nenhuma ação é executada automaticamente — cabe a você aprovar, "
        "ajustar ou rejeitar cada uma abaixo."
    )

    recomendacoes = recomendador.gerar_recomendacoes()
    cor_prioridade = {"alta": "🔴", "media": "🟡", "baixa": "🟢"}

    if not recomendacoes:
        st.write("Nenhuma recomendação gerada para o período selecionado.")

    for indice, rec in enumerate(recomendacoes):
        with st.container(border=True):
            st.markdown(f"{cor_prioridade.get(rec['prioridade'], '⚪')} **[{rec['area']}] {rec['acao']}**")
            st.caption(f"Justificativa da IA: {rec['justificativa']}")

            # 👇 ESTE É O PONTO-CHAVE DO PROJETO: o "checkpoint humano".
            # A recomendação só se torna uma decisão registrada depois
            # que uma pessoa explicitamente clica em um destes botões.
            col_resp, col1, col2, col3 = st.columns([2, 1, 1, 1])
            responsavel = col_resp.text_input(
                "Responsável pela decisão", key=f"responsavel_{indice}", placeholder="Seu nome"
            )

            if col1.button("✅ Aprovar", key=f"aprovar_{indice}"):
                if responsavel:
                    validador.registrar_decisao(rec, "aprovado", responsavel)
                    st.success("Decisão registrada: aprovado.")
                else:
                    st.warning("Informe o responsável antes de registrar a decisão.")

            if col2.button("✏️ Ajustar", key=f"ajustar_{indice}"):
                if responsavel:
                    validador.registrar_decisao(rec, "ajustado", responsavel)
                    st.info("Decisão registrada: ajustado (revisão manual necessária).")
                else:
                    st.warning("Informe o responsável antes de registrar a decisão.")

            if col3.button("❌ Rejeitar", key=f"rejeitar_{indice}"):
                if responsavel:
                    validador.registrar_decisao(rec, "rejeitado", responsavel)
                    st.error("Decisão registrada: rejeitado.")
                else:
                    st.warning("Informe o responsável antes de registrar a decisão.")

    st.divider()
    st.subheader("📋 Histórico de Decisões Humanas (nesta sessão)")

    historico = validador.obter_historico()
    if historico:
        exibir_tabela(pd.DataFrame(historico))
        estatisticas = validador.calcular_estatisticas()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de decisões", estatisticas["total"])
        col2.metric("Aprovadas", estatisticas["aprovados"])
        col3.metric("Ajustadas", estatisticas["ajustados"])
        col4.metric("Rejeitadas", estatisticas["rejeitados"])
    else:
        st.write("Nenhuma decisão registrada ainda nesta sessão.")


# ------------------------------------------------------------------
# ABA 4 — ASSISTENTE ADMINISTRATIVO (tarefas rotineiras)
# ------------------------------------------------------------------
with aba_assistente:
    st.subheader("🗂️ Assistente para Tarefas Administrativas Rotineiras")
    st.caption(
        "Pequenas automações que economizam tempo em tarefas repetitivas do "
        "dia a dia administrativo — sempre entregando um RASCUNHO para revisão humana."
    )

    tarefa = st.selectbox(
        "Selecione a tarefa",
        [
            "Gerar rascunho de e-mail de cobrança de meta",
            "Gerar rascunho de pedido de reposição de estoque",
            "Calcular rateio simples de comissão sobre vendas",
        ],
    )

    if tarefa == "Gerar rascunho de e-mail de cobrança de meta":
        vendedores_lista = analisador.faturamento_por_vendedor()["vendedor"].tolist()
        vendedor_escolhido = st.selectbox("Vendedor", vendedores_lista)
        linha = analisador.faturamento_por_vendedor()
        dados_vendedor = linha[linha["vendedor"] == vendedor_escolhido].iloc[0]

        rascunho = (
            f"Assunto: Acompanhamento de metas — {vendedor_escolhido}\n\n"
            f"Olá {vendedor_escolhido},\n\n"
            f"Fazendo um acompanhamento do desempenho no período: o faturamento "
            f"acumulado está em {formatar_moeda(dados_vendedor['faturamento'])}, frente a uma "
            f"meta de referência de {formatar_moeda(dados_vendedor['meta_mensal'])}.\n\n"
            f"Podemos conversar sobre um plano de ação para o restante do período?\n\n"
            f"Atenciosamente,\n[Seu nome]"
        )
        st.text_area("📝 Rascunho gerado (revise antes de enviar)", rascunho, height=220)
        st.caption("⚠️ Este é apenas um rascunho automático. Revise o tom e o conteúdo antes de enviar.")

    elif tarefa == "Gerar rascunho de pedido de reposição de estoque":
        estoque_baixo = analisador.produtos_estoque_baixo()
        if estoque_baixo.empty:
            st.success("Não há produtos com estoque baixo no momento — nenhum pedido necessário.")
        else:
            itens = "\n".join(
                f"- {linha['produto']}: estoque atual {int(linha['estoque_atual'])}, "
                f"mínimo recomendado {int(linha['estoque_minimo'])}"
                for _, linha in estoque_baixo.iterrows()
            )
            rascunho = (
                "Assunto: Solicitação de reposição de estoque\n\n"
                "Prezado(a) fornecedor(a),\n\n"
                "Solicitamos cotação e reposição para os seguintes itens, que estão "
                "no limite ou abaixo do estoque mínimo:\n\n"
                f"{itens}\n\n"
                "Aguardamos retorno com prazos e valores.\n\n"
                "Atenciosamente,\n[Seu nome]"
            )
            st.text_area("📝 Rascunho gerado (revise antes de enviar)", rascunho, height=220)
            st.caption("⚠️ Confirme as quantidades exatas com o setor de estoque antes de enviar o pedido oficial.")

    elif tarefa == "Calcular rateio simples de comissão sobre vendas":
        percentual_comissao = st.slider("Percentual de comissão (%)", min_value=0.5, max_value=10.0, value=3.0, step=0.5)
        vendedores_resumo = analisador.faturamento_por_vendedor().copy()
        vendedores_resumo["comissao_estimada"] = vendedores_resumo["faturamento"] * (percentual_comissao / 100)
        vendedores_resumo["comissao_estimada_fmt"] = vendedores_resumo["comissao_estimada"].apply(formatar_moeda)
        vendedores_resumo["faturamento_fmt"] = vendedores_resumo["faturamento"].apply(formatar_moeda)

        exibir_tabela(
            vendedores_resumo[["vendedor", "faturamento_fmt", "comissao_estimada_fmt"]].rename(columns={
                "vendedor": "Vendedor",
                "faturamento_fmt": "Faturamento no período",
                "comissao_estimada_fmt": f"Comissão estimada ({percentual_comissao}%)",
            })
        )
        st.caption(
            "⚠️ Cálculo simplificado para fins didáticos. Em um cenário real, "
            "considere regras contratuais específicas (comissão escalonada, "
            "descontos, impostos etc.) e sempre valide com o setor financeiro."
        )


# ============================================================
# RODAPÉ
# ============================================================
st.divider()
st.caption(
    "Projeto didático — Agente Analista Administrativo | "
    "IA aplicada à Administração, com controle humano em todas as decisões."
)
