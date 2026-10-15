"""Gráficos (R6, R7, R8). Cada função devolve uma ``Figure`` sem chamar ``plt.show()``."""

from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from .analises import FREQUENCIAS, listar_remetentes, mensagens_por_dia, mensagens_por_periodo

FORMATO_DATA = mdates.DateFormatter("%d/%m/%y")
LIMIAR_AUTOPCT = 3.0  # % mínimo para escrever o percentual dentro da fatia


def paleta_remetentes(remetentes: list[str]) -> dict[str, tuple]:
    """Cor fixa por remetente, na ordem recebida (use a ordem do resumo)."""
    n = len(remetentes)
    if n <= 10:
        cores = plt.get_cmap("tab10").colors[:n]
    elif n <= 20:
        cores = plt.get_cmap("tab20").colors[:n]
    else:
        turbo = plt.get_cmap("turbo")
        cores = [turbo(0.05 + 0.9 * i / (n - 1)) for i in range(n)]
    return {r: tuple(c) for r, c in zip(remetentes, cores)}


def _formatar_eixo_datas(ax) -> None:
    ax.xaxis.set_major_formatter(FORMATO_DATA)
    for rotulo in ax.get_xticklabels():
        rotulo.set_rotation(45)
        rotulo.set_horizontalalignment("right")


def grafico_historico_remetente(df: pd.DataFrame, remetente: str | None = None) -> Figure:
    """R6 — mensagens por dia de um remetente ou, com ``None``, de todos (small multiples)."""
    remetentes = listar_remetentes(df)
    cores = paleta_remetentes(remetentes)

    if remetente is not None:
        serie = mensagens_por_dia(df, remetente)
        fig, ax = plt.subplots(figsize=(11, 4))
        ax.bar(serie.index, serie.to_numpy(), width=1.0, color=cores[remetente])
        ax.set_title(f"Mensagens por dia — {remetente}")
        ax.set_xlabel("Data")
        ax.set_ylabel("Quantidade de mensagens")
        ax.set_xlim(serie.index.min() - pd.Timedelta(days=1), serie.index.max() + pd.Timedelta(days=1))
        _formatar_eixo_datas(ax)
        fig.tight_layout()
        return fig

    n = len(remetentes)
    fig, eixos = plt.subplots(n, 1, figsize=(11, max(1.6 * n, 3)), sharex=True, squeeze=False)
    for ax, nome in zip(eixos[:, 0], remetentes):
        serie = mensagens_por_dia(df, nome)
        ax.bar(serie.index, serie.to_numpy(), width=1.0, color=cores[nome])
        ax.set_title(f"{nome} ({int(serie.sum())})", fontsize=9, loc="left")
        ax.tick_params(axis="y", labelsize=8)
    ultimo = eixos[-1, 0]
    ultimo.set_xlabel("Data")
    _formatar_eixo_datas(ultimo)
    fig.suptitle("Mensagens por dia — todos os remetentes")
    fig.supylabel("Quantidade de mensagens")
    fig.tight_layout()
    return fig


def _numero_br(valor: float) -> str:
    return f"{valor:.1f}".replace(".", ",")


def grafico_pizza(df: pd.DataFrame) -> Figure:
    """R7 — percentual de mensagens de cada remetente."""
    contagem = df["remetente"].value_counts()
    remetentes = listar_remetentes(df)
    contagem = contagem.reindex(remetentes)
    cores = paleta_remetentes(remetentes)
    total = contagem.sum()

    fig, ax = plt.subplots(figsize=(10, 6))
    fatias, _, _ = ax.pie(
        contagem.to_numpy(),
        colors=[cores[r] for r in remetentes],
        startangle=90,
        counterclock=False,
        autopct=lambda p: f"{_numero_br(p)} %" if p >= LIMIAR_AUTOPCT else "",
        pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 1},
    )
    rotulos = [
        f"{nome} — {_numero_br(qtd / total * 100)} % ({qtd})" for nome, qtd in contagem.items()
    ]
    ax.legend(fatias, rotulos, title="Remetente", loc="center left", bbox_to_anchor=(1.0, 0.5))
    ax.set_title(f"Percentual de mensagens por remetente (total: {total})")
    ax.axis("equal")
    fig.tight_layout()
    return fig


def grafico_linhas(df: pd.DataFrame, freq: str = "D") -> Figure:
    """R8 — mensagens ao longo do tempo, uma linha (e cor) por remetente."""
    tabela = mensagens_por_periodo(df, freq)
    cores = paleta_remetentes(list(tabela.columns))

    fig, ax = plt.subplots(figsize=(12, 5))
    for nome in tabela.columns:
        ax.plot(tabela.index, tabela[nome].to_numpy(), label=nome, color=cores[nome],
                linewidth=1.4, marker="o" if freq == "MS" else None, markersize=4)
    ax.set_title(f"Mensagens ao longo do tempo por remetente (agrupado por {FREQUENCIAS[freq].lower()})")
    ax.set_xlabel("Data")
    ax.set_ylabel("Quantidade de mensagens")
    ax.grid(alpha=0.3)
    ax.legend(title="Remetente", bbox_to_anchor=(1.01, 1), loc="upper left")
    _formatar_eixo_datas(ax)
    fig.tight_layout()
    return fig
