# -*- coding: utf-8 -*-
"""
agent/recommender.py
=====================

MÓDULO DE RECOMENDAÇÕES (as "sugestões" do agente)
----------------------------------------------------
Diferente do Módulo de Relatórios (que descreve O QUE aconteceu),
este módulo sugere O QUE PODERIA SER FEITO a respeito — mas sempre
como SUGESTÃO, nunca como ordem automática.

Cada recomendação é acompanhada de:
  - a ação sugerida;
  - a justificativa (por que a IA sugere isso, com base em quais dados);
  - o nível de prioridade.

É fundamental destacar aos alunos: o agente aqui está fazendo o
trabalho de "triagem" — organizando e priorizando informação para
facilitar a vida do gestor — mas a decisão final (comprar mais
estoque, remanejar um vendedor, lançar uma promoção) é sempre humana.
Essa fronteira é reforçada visualmente na interface e formalizada no
Módulo de Validação Humana (agent/validator.py).
"""

import pandas as pd


class RecomendadorIA:
    """
    Gera sugestões de ação a partir de padrões identificados nos
    dados (estoque, desempenho de vendas, metas).
    """

    def __init__(self, df: pd.DataFrame, analisador):
        self.df = df
        self.analisador = analisador

    def gerar_recomendacoes(self) -> list:
        """
        Retorna uma lista de recomendações, cada uma um dicionário com:
          - prioridade: 'alta', 'media' ou 'baixa'
          - acao: o que se sugere fazer
          - justificativa: com base em quais dados a sugestão foi gerada
          - area: setor/área administrativa relacionada (Estoque, Vendas, Comercial...)
        """
        recomendacoes = []

        # --- Recomendação: reposição de estoque ---
        estoque_baixo = self.analisador.produtos_estoque_baixo()
        for _, linha in estoque_baixo.iterrows():
            recomendacoes.append({
                "prioridade": "alta",
                "area": "Estoque",
                "acao": f"Avaliar reposição do produto '{linha['produto']}'.",
                "justificativa": (
                    f"Estoque atual ({int(linha['estoque_atual'])} un.) está no limite ou "
                    f"abaixo do mínimo recomendado ({int(linha['estoque_minimo'])} un.)."
                ),
            })

        # --- Recomendação: produtos parados (giro baixo) ---
        giro = self.analisador.calcular_giro_estoque()
        parados = giro[giro["giro_estoque"] < 0.3].head(3)
        for _, linha in parados.iterrows():
            recomendacoes.append({
                "prioridade": "media",
                "area": "Comercial",
                "acao": (
                    f"Avaliar ação comercial (promoção, vitrine, combo) para o "
                    f"produto '{linha['produto']}'."
                ),
                "justificativa": (
                    f"Produto com giro de estoque baixo ({linha['giro_estoque']:.2f}), "
                    f"indicando possível excesso de estoque parado."
                ),
            })

        # --- Recomendação: apoio a vendedores abaixo da meta ---
        vendedores = self.analisador.faturamento_por_vendedor()
        abaixo_meta = vendedores[vendedores["faturamento"] < vendedores["meta_mensal"]]
        for _, linha in abaixo_meta.iterrows():
            diferenca = linha["meta_mensal"] - linha["faturamento"]
            recomendacoes.append({
                "prioridade": "alta" if diferenca > linha["meta_mensal"] * 0.3 else "media",
                "area": "Gestão de Vendas",
                "acao": (
                    f"Conversar com {linha['vendedor']} sobre plano de ação para "
                    f"atingir a meta."
                ),
                "justificativa": (
                    f"Faturamento acumulado está {diferenca:,.2f} abaixo da meta "
                    f"de referência no período analisado."
                ),
            })

        # --- Recomendação: reforçar categoria/produto de destaque ---
        por_categoria = self.analisador.faturamento_por_categoria()
        if len(por_categoria) > 0:
            categoria_top = por_categoria.iloc[0]
            recomendacoes.append({
                "prioridade": "baixa",
                "area": "Comercial",
                "acao": (
                    f"Considerar ampliar o mix ou destaque da categoria "
                    f"'{categoria_top['categoria']}' em campanhas futuras."
                ),
                "justificativa": (
                    "Categoria com melhor desempenho de faturamento no período analisado."
                ),
            })

        # Ordena por prioridade (alta > media > baixa) para facilitar a leitura
        ordem_prioridade = {"alta": 0, "media": 1, "baixa": 2}
        recomendacoes.sort(key=lambda r: ordem_prioridade.get(r["prioridade"], 3))

        return recomendacoes
