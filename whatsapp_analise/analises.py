"""Análises em tabela. As funções não alteram o DataFrame recebido."""

import pandas as pd

# Agrupamentos aceitos pelo gráfico de linhas
FREQUENCIAS = {"D": "Dia", "W": "Semana", "MS": "Mês"}


def resumo_conversas(df):
    """R4 - total de mensagens por remetente, do maior para o menor."""
    resumo = df["remetente"].value_counts().reset_index()
    resumo.columns = ["remetente", "total_mensagens"]

    # Em caso de empate, ordem alfabética
    resumo = resumo.sort_values(
        ["total_mensagens", "remetente"], ascending=[False, True]
    ).reset_index(drop=True)

    resumo["percentual"] = (resumo["total_mensagens"] / len(df) * 100).round(1)

    # Índice começando em 1 = posição no ranking
    resumo.index = resumo.index + 1
    return resumo


def listar_remetentes(df):
    """Remetentes do mais ativo para o menos ativo."""
    return resumo_conversas(df)["remetente"].tolist()


def historico_remetente(df, remetente):
    """R5 - mensagens de um remetente, com data e hora, em ordem cronológica."""
    if remetente not in df["remetente"].values:
        raise KeyError(f"Remetente não encontrado na conversa: {remetente}")

    historico = df[df["remetente"] == remetente]
    historico = historico[["data", "hora", "mensagem"]]
    return historico.reset_index(drop=True)


def mensagens_por_dia(df, remetente=None):
    """Mensagens por dia em todo o período da conversa (dias sem mensagem = 0)."""
    todos_os_dias = pd.date_range(df["data"].min(), df["data"].max(), freq="D")

    if remetente is not None:
        if remetente not in df["remetente"].values:
            raise KeyError(f"Remetente não encontrado na conversa: {remetente}")
        df = df[df["remetente"] == remetente]

    por_dia = df.set_index("data").resample("D").size()
    por_dia = por_dia.reindex(todos_os_dias, fill_value=0)
    por_dia.index.name = "data"
    por_dia.name = "mensagens"
    return por_dia


def mensagens_por_periodo(df, freq="D"):
    """Tabela com uma linha por período e uma coluna por remetente.

    freq: "D" (dia), "W" (semana) ou "MS" (mês).
    """
    if freq not in FREQUENCIAS:
        raise ValueError(f"freq deve ser 'D', 'W' ou 'MS', não {freq!r}")

    contagem = df.groupby([pd.Grouper(key="data", freq=freq), "remetente"]).size()
    tabela = contagem.unstack("remetente", fill_value=0)

    # resample().sum() acrescenta os períodos sem nenhuma mensagem, com 0
    tabela = tabela.resample(freq).sum()

    # Colunas na ordem do resumo (mais ativo primeiro)
    tabela = tabela[listar_remetentes(df)]
    return tabela
