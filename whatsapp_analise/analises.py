"""Análises tabulares (funções puras: recebem o DataFrame e devolvem um novo)."""

from __future__ import annotations

import pandas as pd

FREQUENCIAS = {"D": "Dia", "W": "Semana", "MS": "Mês"}


def resumo_conversas(df: pd.DataFrame) -> pd.DataFrame:
    """R4 — total de mensagens por remetente, do maior para o menor."""
    contagem = df.groupby("remetente").size()
    resumo = (
        pd.DataFrame(
            {"remetente": contagem.index.astype("str"), "total_mensagens": contagem.to_numpy()}
        )
        .sort_values(["total_mensagens", "remetente"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )
    total = resumo["total_mensagens"].sum()
    resumo = resumo.assign(
        percentual=(resumo["total_mensagens"] / total * 100).round(1) if total else 0.0
    )
    resumo.index = pd.RangeIndex(1, len(resumo) + 1)
    return resumo


def listar_remetentes(df: pd.DataFrame) -> list[str]:
    """Remetentes na ordem do resumo (mais ativo primeiro)."""
    return resumo_conversas(df)["remetente"].tolist()


def historico_remetente(df: pd.DataFrame, remetente: str) -> pd.DataFrame:
    """R5 — mensagens de um remetente, com data e hora, em ordem cronológica."""
    if remetente not in set(df["remetente"]):
        raise KeyError(f"Remetente não encontrado na conversa: {remetente!r}")
    filtrado = df.loc[df["remetente"] == remetente, ["data", "hora", "mensagem"]]
    return filtrado.sort_values(["data", "hora"], kind="stable").reset_index(drop=True)


def _periodo_completo(df: pd.DataFrame, freq: str) -> pd.DatetimeIndex:
    inicio = df["data"].min()
    fim = df["data"].max()
    if freq == "W":
        return pd.date_range(inicio.to_period("W").end_time.normalize(),
                             fim.to_period("W").end_time.normalize(), freq="W")
    if freq == "MS":
        return pd.date_range(inicio.to_period("M").start_time, fim, freq="MS")
    return pd.date_range(inicio, fim, freq="D")


def mensagens_por_dia(df: pd.DataFrame, remetente: str | None = None) -> pd.Series:
    """Mensagens por dia em todo o período da conversa, com zeros nos dias vazios.

    Com ``remetente``, conta só as mensagens dele, mas o eixo de dias continua
    cobrindo a conversa inteira (para comparar remetentes lado a lado).
    """
    dias = _periodo_completo(df, "D")
    if remetente is not None:
        if remetente not in set(df["remetente"]):
            raise KeyError(f"Remetente não encontrado na conversa: {remetente!r}")
        df = df.loc[df["remetente"] == remetente]
    serie = df.set_index("data").resample("D").size()
    serie = serie.reindex(dias, fill_value=0).astype("int64")
    serie.index.name = "data"
    serie.name = "mensagens"
    return serie


def mensagens_por_periodo(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    """Tabela data × remetente com a contagem de mensagens (zeros preenchidos).

    ``freq``: ``"D"`` (dia), ``"W"`` (semana, terminando no domingo) ou ``"MS"`` (mês).
    """
    if freq not in FREQUENCIAS:
        raise ValueError(f"freq deve ser um de {sorted(FREQUENCIAS)}, não {freq!r}")
    tabela = (
        df.groupby([pd.Grouper(key="data", freq=freq), "remetente"])
        .size()
        .unstack("remetente", fill_value=0)
    )
    tabela = tabela.reindex(index=_periodo_completo(df, freq), fill_value=0)
    tabela = tabela.reindex(columns=listar_remetentes(df), fill_value=0).astype("int64")
    tabela.index.name = "data"
    tabela.columns.name = "remetente"
    return tabela
