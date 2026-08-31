# -*- coding: utf-8 -*-
"""
agent/analyzer.py
==================

MÓDULO DE ANÁLISE (o "olho" do agente)
---------------------------------------
Este módulo é responsável por transformar dados brutos (a tabela de
vendas/estoque) em números que fazem sentido para a gestão: os KPIs
(Key Performance Indicators / Indicadores-Chave de Desempenho).

Importante para a apresentação: este módulo NUNCA toma decisões.
Ele apenas calcula e organiza fatos a partir dos dados. Quem decide o
que fazer com esses fatos é sempre um humano — isso é reforçado mais
adiante no módulo de validação (agent/validator.py).

Bibliotecas usadas:
- pandas: para manipular tabelas de dados (agrupar, somar, filtrar).
- plotly.express: para criar gráficos interativos (o usuário pode dar
  zoom, passar o mouse para ver valores exatos, etc.), o que é mais
  rico que um gráfico estático.
"""

import pandas as pd
import plotly.express as px


class AnalisadorDados:
    """
    Classe responsável por calcular os indicadores (KPIs) e montar os
    gráficos a partir da base de dados de vendas/estoque.

    Usamos uma "classe" (em vez de funções soltas) porque assim
    conseguimos guardar o DataFrame carregado uma única vez em
    `self.df` e reaproveitar em vários métodos, sem precisar
    repassá-lo toda hora.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    # ------------------------------------------------------------------
    # KPI 1: FATURAMENTO
    # ------------------------------------------------------------------
    def calcular_faturamento_total(self) -> float:
        """
        Faturamento total = soma de todos os valores vendidos
        (coluna 'valor_total') no período analisado.
        """
        return float(self.df["valor_total"].sum())

    def calcular_faturamento_por_periodo(self, frequencia: str = "ME") -> pd.DataFrame:
        """
        Agrupa o faturamento por período de tempo.

        frequencia:
            'D' = diário, 'W' = semanal, 'ME' = mensal (fim de mês)

        Isso é o que permite ao gestor enxergar TENDÊNCIA (o
        faturamento está subindo ou caindo?), e não apenas o número
        total acumulado.
        """
        df_temp = self.df.set_index("data")
        faturamento = df_temp["valor_total"].resample(frequencia).sum().reset_index()
        faturamento.columns = ["periodo", "faturamento"]
        return faturamento

    # ------------------------------------------------------------------
    # KPI 2: TICKET MÉDIO
    # ------------------------------------------------------------------
    def calcular_ticket_medio(self) -> float:
        """
        Ticket médio = faturamento total / número de vendas (transações).

        É um indicador clássico de administração: mostra, em média,
        quanto cada venda "vale". Um ticket médio caindo pode indicar
        que os clientes estão comprando menos por vez, mesmo que o
        número de vendas continue igual.
        """
        numero_vendas = len(self.df)
        if numero_vendas == 0:
            return 0.0
        return float(self.df["valor_total"].sum() / numero_vendas)

    # ------------------------------------------------------------------
    # KPI 3: GIRO DE ESTOQUE
    # ------------------------------------------------------------------
    def calcular_giro_estoque(self) -> pd.DataFrame:
        """
        Giro de estoque (simplificado para fins didáticos) =
        quantidade total vendida de um produto / estoque atual dele.

        Um giro ALTO significa que o produto vende rápido em relação
        ao que se tem em estoque (bom sinal, mas atenção para não
        faltar produto). Um giro BAIXO pode indicar excesso de
        estoque parado (capital empatado).

        Na prática de administração, o giro de estoque "oficial" usa o
        estoque médio do período; aqui simplificamos para o estoque
        atual, que é a informação disponível no dataset de exemplo —
        vale explicar essa simplificação aos alunos.
        """
        resumo = (
            self.df.groupby("produto")
            .agg(
                quantidade_total_vendida=("quantidade_vendida", "sum"),
                estoque_atual=("estoque_atual", "last"),
                estoque_minimo=("estoque_minimo", "last"),
            )
            .reset_index()
        )
        # Evita divisão por zero
        resumo["giro_estoque"] = resumo.apply(
            lambda linha: linha["quantidade_total_vendida"] / linha["estoque_atual"]
            if linha["estoque_atual"] > 0
            else linha["quantidade_total_vendida"],
            axis=1,
        )
        return resumo.sort_values("giro_estoque", ascending=False)

    # ------------------------------------------------------------------
    # AGRUPAMENTOS AUXILIARES
    # ------------------------------------------------------------------
    def faturamento_por_categoria(self) -> pd.DataFrame:
        return (
            self.df.groupby("categoria")["valor_total"]
            .sum()
            .reset_index()
            .sort_values("valor_total", ascending=False)
        )

    def faturamento_por_vendedor(self) -> pd.DataFrame:
        resumo = self.df.groupby("vendedor").agg(
            faturamento=("valor_total", "sum"),
            meta_mensal=("meta_mensal_vendedor", "first"),
        ).reset_index()
        return resumo

    def produtos_estoque_baixo(self) -> pd.DataFrame:
        """
        Retorna os produtos cujo estoque atual está igual ou abaixo
        do estoque mínimo definido — a base para o sistema de alertas.
        """
        estoque = self.df.groupby("produto").agg(
            estoque_atual=("estoque_atual", "last"),
            estoque_minimo=("estoque_minimo", "last"),
        ).reset_index()
        return estoque[estoque["estoque_atual"] <= estoque["estoque_minimo"]]

    # ------------------------------------------------------------------
    # GRÁFICOS (Plotly)
    # ------------------------------------------------------------------
    def grafico_faturamento_periodo(self, frequencia: str = "ME"):
        dados = self.calcular_faturamento_por_periodo(frequencia)
        fig = px.line(
            dados,
            x="periodo",
            y="faturamento",
            markers=True,
            title="Evolução do Faturamento",
            labels={"periodo": "Período", "faturamento": "Faturamento (R$)"},
        )
        fig.update_layout(template="plotly_white")
        return fig

    def grafico_faturamento_categoria(self):
        dados = self.faturamento_por_categoria()
        fig = px.bar(
            dados,
            x="categoria",
            y="valor_total",
            title="Faturamento por Categoria",
            labels={"categoria": "Categoria", "valor_total": "Faturamento (R$)"},
            color="categoria",
        )
        fig.update_layout(template="plotly_white", showlegend=False)
        return fig

    def grafico_desempenho_vendedores(self):
        dados = self.faturamento_por_vendedor()
        fig = px.bar(
            dados,
            x="vendedor",
            y=["faturamento", "meta_mensal"],
            barmode="group",
            title="Faturamento x Meta por Vendedor (acumulado no período)",
            labels={"value": "Valor (R$)", "vendedor": "Vendedor", "variable": "Indicador"},
        )
        fig.update_layout(template="plotly_white")
        return fig

    def grafico_giro_estoque(self):
        dados = self.calcular_giro_estoque()
        fig = px.bar(
            dados,
            x="produto",
            y="giro_estoque",
            title="Giro de Estoque por Produto",
            labels={"produto": "Produto", "giro_estoque": "Giro (qtd. vendida / estoque atual)"},
            color="giro_estoque",
            color_continuous_scale="Blues",
        )
        fig.update_layout(template="plotly_white", xaxis_tickangle=-30)
        return fig
