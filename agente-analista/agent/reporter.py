# -*- coding: utf-8 -*-
"""
agent/reporter.py
==================

MÓDULO DE RELATÓRIOS (a "voz" do agente)
------------------------------------------
Este módulo pega os números calculados pelo Módulo de Análise
(agent/analyzer.py) e os transforma em TEXTO — frases em português
claro, do tipo que apareceria em um relatório executivo real.

Ponto pedagógico importante: isto NÃO é "inteligência artificial
generativa" tentando adivinhar informações. É um sistema baseado em
REGRAS: comparamos números com limites (thresholds) definidos e
escolhemos frases prontas de acordo com o resultado. Isso é
proposital para o projeto didático, porque deixa 100% transparente
COMO cada insight foi gerado — não há "caixa preta".

Se quisessem evoluir o projeto no futuro, essas regras poderiam ser
substituídas por chamadas a um modelo de linguagem (como a API da
Anthropic), mas o princípio de "auxiliar, não substituir" o humano
continuaria o mesmo.
"""

import pandas as pd
from utils.helpers import formatar_moeda, formatar_percentual


class GeradorRelatorios:
    """
    Gera o relatório executivo em texto a partir dos dados e dos
    KPIs já calculados pelo AnalisadorDados.
    """

    def __init__(self, df: pd.DataFrame, analisador):
        self.df = df
        self.analisador = analisador

    def gerar_resumo_executivo(self) -> dict:
        """
        Monta um dicionário com as principais seções do relatório
        executivo. Retornamos um dicionário (e não só um texto único)
        para que a interface (app.py) possa exibir cada seção em um
        cartão/bloco visual separado.
        """
        faturamento_total = self.analisador.calcular_faturamento_total()
        ticket_medio = self.analisador.calcular_ticket_medio()
        numero_vendas = len(self.df)

        periodo_inicio = self.df["data"].min().strftime("%d/%m/%Y")
        periodo_fim = self.df["data"].max().strftime("%d/%m/%Y")

        categoria_top = self.analisador.faturamento_por_categoria().iloc[0]
        vendedores = self.analisador.faturamento_por_vendedor().sort_values(
            "faturamento", ascending=False
        )
        vendedor_top = vendedores.iloc[0]

        texto_introducao = (
            f"No período de {periodo_inicio} a {periodo_fim}, foram registradas "
            f"{numero_vendas} vendas, totalizando {formatar_moeda(faturamento_total)} "
            f"em faturamento. O ticket médio por venda foi de {formatar_moeda(ticket_medio)}."
        )

        texto_destaques = (
            f"A categoria com maior faturamento foi '{categoria_top['categoria']}', "
            f"com {formatar_moeda(categoria_top['valor_total'])} em vendas. "
            f"O vendedor com melhor desempenho foi {vendedor_top['vendedor']}, "
            f"responsável por {formatar_moeda(vendedor_top['faturamento'])} no período."
        )

        return {
            "periodo": f"{periodo_inicio} a {periodo_fim}",
            "faturamento_total": faturamento_total,
            "ticket_medio": ticket_medio,
            "numero_vendas": numero_vendas,
            "texto_introducao": texto_introducao,
            "texto_destaques": texto_destaques,
        }

    def gerar_insights_automaticos(self) -> list:
        """
        Analisa os dados sob diferentes ângulos e devolve uma lista de
        "insights" (observações relevantes), cada um com:
          - tipo: 'positivo', 'atencao' ou 'critico' (usado para cor/ícone na tela)
          - titulo: frase curta
          - descricao: explicação com números

        Esta é a etapa que mais se parece com "IA" aos olhos do
        usuário, mas — repetindo o ponto pedagógico — é feita com
        REGRAS DE NEGÓCIO claras e auditáveis, não "caixa-preta".
        """
        insights = []

        # --- Insight sobre tendência de faturamento (mês atual x mês anterior) ---
        faturamento_mensal = self.analisador.calcular_faturamento_por_periodo("ME")
        if len(faturamento_mensal) >= 2:
            mes_atual = faturamento_mensal.iloc[-1]["faturamento"]
            mes_anterior = faturamento_mensal.iloc[-2]["faturamento"]
            if mes_anterior > 0:
                variacao = ((mes_atual - mes_anterior) / mes_anterior) * 100
                if variacao >= 5:
                    insights.append({
                        "tipo": "positivo",
                        "titulo": "Faturamento em crescimento",
                        "descricao": (
                            f"O faturamento do último mês analisado cresceu "
                            f"{formatar_percentual(variacao)} em relação ao mês anterior."
                        ),
                    })
                elif variacao <= -5:
                    insights.append({
                        "tipo": "critico",
                        "titulo": "Queda no faturamento",
                        "descricao": (
                            f"O faturamento do último mês caiu "
                            f"{formatar_percentual(abs(variacao))} em relação ao mês anterior. "
                            f"Recomenda-se investigar a causa."
                        ),
                    })
                else:
                    insights.append({
                        "tipo": "atencao",
                        "titulo": "Faturamento estável",
                        "descricao": (
                            f"O faturamento variou apenas {formatar_percentual(variacao)} "
                            f"em relação ao mês anterior, sem tendência clara de alta ou baixa."
                        ),
                    })

        # --- Insight sobre concentração de faturamento em poucas categorias ---
        por_categoria = self.analisador.faturamento_por_categoria()
        total = por_categoria["valor_total"].sum()
        if total > 0:
            participacao_top = por_categoria.iloc[0]["valor_total"] / total * 100
            if participacao_top >= 50:
                insights.append({
                    "tipo": "atencao",
                    "titulo": "Concentração de faturamento em uma categoria",
                    "descricao": (
                        f"A categoria '{por_categoria.iloc[0]['categoria']}' responde por "
                        f"{formatar_percentual(participacao_top)} do faturamento total. "
                        f"Alta dependência de uma única categoria pode representar risco."
                    ),
                })

        # --- Insight sobre vendedores abaixo da meta ---
        vendedores = self.analisador.faturamento_por_vendedor()
        abaixo_meta = vendedores[vendedores["faturamento"] < vendedores["meta_mensal"]]
        if len(abaixo_meta) > 0:
            nomes = ", ".join(abaixo_meta["vendedor"].tolist())
            insights.append({
                "tipo": "critico",
                "titulo": "Vendedores abaixo da meta acumulada",
                "descricao": (
                    f"{len(abaixo_meta)} vendedor(es) estão com faturamento acumulado "
                    f"abaixo da meta mensal de referência: {nomes}."
                ),
            })

        # --- Insight sobre estoque baixo ---
        estoque_baixo = self.analisador.produtos_estoque_baixo()
        if len(estoque_baixo) > 0:
            nomes_produtos = ", ".join(estoque_baixo["produto"].tolist())
            insights.append({
                "tipo": "critico",
                "titulo": "Produtos com estoque no limite ou abaixo do mínimo",
                "descricao": (
                    f"{len(estoque_baixo)} produto(s) estão com estoque igual ou "
                    f"inferior ao mínimo recomendado: {nomes_produtos}."
                ),
            })

        # --- Insight sobre giro de estoque baixo (capital parado) ---
        giro = self.analisador.calcular_giro_estoque()
        giro_baixo = giro[giro["giro_estoque"] < 0.5]
        if len(giro_baixo) > 0:
            insights.append({
                "tipo": "atencao",
                "titulo": "Produtos com baixo giro de estoque",
                "descricao": (
                    f"{len(giro_baixo)} produto(s) apresentam giro de estoque baixo, "
                    f"o que pode indicar capital parado em itens de pouca saída."
                ),
            })

        return insights
