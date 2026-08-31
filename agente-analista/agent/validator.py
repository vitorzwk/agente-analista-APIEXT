# -*- coding: utf-8 -*-
"""
agent/validator.py
====================

MÓDULO DE VALIDAÇÃO HUMANA (o "freio de mão" do agente)
----------------------------------------------------------
Este é o módulo mais importante do ponto de vista conceitual do
projeto. Ele existe para deixar explícito, em código e na interface,
que o agente de IA NÃO executa ações sozinho: ele só registra
SUGESTÕES pendentes, que precisam ser aprovadas, ajustadas ou
rejeitadas por uma pessoa responsável.

Isso ilustra, de forma prática, o conceito de "Human-in-the-loop"
(humano no circuito de decisão) — um princípio central quando se fala
em uso responsável de Inteligência Artificial em ambientes
corporativos, especialmente em decisões administrativas e financeiras
que têm impacto real (comprar estoque, remanejar pessoas, gastar
dinheiro).

Nesta versão didática, guardamos o histórico de decisões apenas na
MEMÓRIA da sessão do Streamlit (st.session_state) — ou seja, ele se
perde ao recarregar a página. Isso é proposital para manter o projeto
simples; em um sistema real, esse histórico seria salvo em um banco
de dados, criando uma trilha de auditoria (quem aprovou o quê e
quando).
"""

from datetime import datetime


class ValidadorHumano:
    """
    Gerencia o "checkpoint" onde o humano decide o que fazer com cada
    recomendação gerada pela IA (agent/recommender.py).

    O estado (lista de decisões) é injetado de fora (via
    lista_decisoes), tipicamente vindo do st.session_state do
    Streamlit, para que ele persista entre as interações do usuário
    dentro da mesma sessão do dashboard.
    """

    def __init__(self, lista_decisoes: list):
        # lista_decisoes é uma referência à lista guardada em
        # st.session_state — qualquer alteração feita aqui dentro
        # (append, etc.) reflete diretamente na sessão do Streamlit.
        self.lista_decisoes = lista_decisoes

    def registrar_decisao(self, recomendacao: dict, decisao: str, responsavel: str, observacao: str = "") -> None:
        """
        Registra a decisão humana tomada sobre uma recomendação da IA.

        Parâmetros
        ----------
        recomendacao : dict
            A recomendação original gerada pelo RecomendadorIA.
        decisao : str
            'aprovado', 'rejeitado' ou 'ajustado'.
        responsavel : str
            Nome/identificação de quem tomou a decisão (informado na interface).
        observacao : str
            Comentário opcional justificando a decisão humana.
        """
        registro = {
            "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "acao_sugerida": recomendacao.get("acao", ""),
            "area": recomendacao.get("area", ""),
            "decisao": decisao,
            "responsavel": responsavel,
            "observacao": observacao,
        }
        self.lista_decisoes.append(registro)

    def obter_historico(self) -> list:
        """Retorna o histórico de decisões já registradas nesta sessão."""
        return self.lista_decisoes

    def calcular_estatisticas(self) -> dict:
        """
        Calcula um resumo simples do histórico de decisões — útil para
        mostrar, na interface, o quanto o humano está de fato
        interagindo com as sugestões da IA (e não apenas aceitando
        tudo de forma automática).
        """
        total = len(self.lista_decisoes)
        aprovados = sum(1 for d in self.lista_decisoes if d["decisao"] == "aprovado")
        rejeitados = sum(1 for d in self.lista_decisoes if d["decisao"] == "rejeitado")
        ajustados = sum(1 for d in self.lista_decisoes if d["decisao"] == "ajustado")

        return {
            "total": total,
            "aprovados": aprovados,
            "rejeitados": rejeitados,
            "ajustados": ajustados,
        }
