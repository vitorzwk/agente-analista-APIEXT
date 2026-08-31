# -*- coding: utf-8 -*-
"""
utils/helpers.py
=================

Este arquivo reúne pequenas funções "utilitárias" (helpers) que são usadas
em vários pontos do sistema: formatar números como moeda, formatar
porcentagens e carregar os arquivos de dados enviados pelo usuário.

Separar essas funções em um arquivo próprio é uma boa prática de
programação chamada "DRY" (Don't Repeat Yourself — não se repita):
em vez de escrever o mesmo código de formatação em vários lugares,
escrevemos uma vez aqui e reaproveitamos em todo o projeto.
"""

import pandas as pd


def formatar_moeda(valor: float) -> str:
    """
    Recebe um número (ex: 1234.5) e devolve uma string formatada
    como moeda brasileira (ex: 'R$ 1.234,50').

    Por que isso importa para um Analista Administrativo?
    Porque relatórios executivos precisam apresentar números de forma
    clara e no padrão que o público (diretoria, gestores) está
    acostumado a ler.
    """
    try:
        valor_formatado = f"R$ {valor:,.2f}"
        # Troca os separadores do padrão americano (1,234.50) para o
        # padrão brasileiro (1.234,50)
        valor_formatado = valor_formatado.replace(",", "X").replace(".", ",").replace("X", ".")
        return valor_formatado
    except (ValueError, TypeError):
        return "R$ 0,00"


def formatar_percentual(valor: float, casas_decimais: int = 1) -> str:
    """
    Recebe um número decimal (ex: 0.153) e devolve uma string em
    formato de porcentagem (ex: '15.3%').

    Aqui recebemos o valor já multiplicado por 100 (ex: 15.3), não a
    fração (0.153), para deixar o uso mais intuitivo no restante do
    código.
    """
    try:
        return f"{valor:.{casas_decimais}f}%"
    except (ValueError, TypeError):
        return "0.0%"


def carregar_dados(arquivo) -> pd.DataFrame:
    """
    Carrega um arquivo CSV ou Excel (.xlsx) enviado pelo usuário e
    devolve um DataFrame do pandas (uma "tabela" que o Python entende).

    Este é um ponto importante para os alunos entenderem: a IA não
    "adivinha" os dados, ela precisa que os dados sejam entregues em um
    formato estruturado (linhas e colunas). Por isso, o primeiro passo
    de qualquer análise é sempre a etapa de leitura e organização dos
    dados brutos.

    Parâmetros
    ----------
    arquivo : UploadedFile do Streamlit ou caminho de arquivo (str)

    Retorna
    -------
    pandas.DataFrame ou None em caso de erro
    """
    try:
        nome_arquivo = getattr(arquivo, "name", str(arquivo))

        if nome_arquivo.endswith(".csv"):
            df = pd.read_csv(arquivo)
        elif nome_arquivo.endswith((".xlsx", ".xls")):
            df = pd.read_excel(arquivo)
        else:
            raise ValueError("Formato de arquivo não suportado. Use .csv ou .xlsx")

        # Converte a coluna de data para o tipo datetime do pandas,
        # se ela existir. Isso é essencial para poder agrupar por
        # mês/semana mais adiante.
        if "data" in df.columns:
            df["data"] = pd.to_datetime(df["data"], errors="coerce")

        return df

    except Exception as erro:
        print(f"Erro ao carregar arquivo: {erro}")
        return None


def validar_colunas_necessarias(df: pd.DataFrame, colunas_esperadas: list) -> tuple:
    """
    Verifica se o DataFrame carregado possui as colunas mínimas que o
    agente precisa para funcionar (ex: 'valor_total', 'produto', etc.).

    Retorna uma tupla (esta_valido: bool, colunas_faltando: list).

    Esse tipo de validação é o que chamamos de "guarda de qualidade
    de dados" — antes de deixar a IA analisar algo, garantimos que a
    base está minimamente correta. Isso evita que o agente gere
    conclusões erradas a partir de dados incompletos.
    """
    colunas_faltando = [c for c in colunas_esperadas if c not in df.columns]
    esta_valido = len(colunas_faltando) == 0
    return esta_valido, colunas_faltando


def exibir_tabela(df: pd.DataFrame, use_container_width: bool = True) -> None:
    """
    Exibe um DataFrame na tela do Streamlit, com fallback automático.

    Por padrão, o Streamlit usa a biblioteca 'pyarrow' internamente
    para desenhar tabelas interativas (st.dataframe) — com colunas
    redimensionáveis, ordenação por clique, etc. Em alguns
    computadores corporativos, uma política de segurança do Windows
    (Application Control / AppLocker) bloqueia a DLL do pyarrow por
    ela não estar na lista de programas liberados pela empresa.

    Para o dashboard não quebrar nesses computadores, esta função
    tenta primeiro o modo interativo (st.dataframe) e, se isso falhar
    por causa do pyarrow, usa automaticamente 'st.table', que desenha
    uma tabela estática (sem ordenação por clique, mas 100% funcional)
    sem depender do pyarrow.
    """
    import streamlit as st

    try:
        st.dataframe(df, use_container_width=use_container_width, hide_index=True)
    except ImportError:
        # Ambiente sem pyarrow disponível (ex: política de segurança
        # corporativa bloqueando a DLL) -> usa tabela estática.
        st.table(df.reset_index(drop=True))
