"""Gráficos com seaborn em tema escuro (R6, R7, R8).

Cada função devolve uma Figure do matplotlib, sem chamar plt.show().
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .analises import FREQUENCIAS, listar_remetentes, mensagens_por_periodo

# ---------------------------------------------------------------------------
# Tema escuro "grafite"
# ---------------------------------------------------------------------------
FUNDO_FIGURA = "#1E1F24"
FUNDO_GRAFICO = "#26282E"
TEXTO = "#E6E6E6"
TEXTO_SECUNDARIO = "#A9ADB7"
GRADE = "#3A3D45"

# Uma cor por remetente, na ordem do resumo (mais ativo primeiro).
# Todas têm contraste de pelo menos 5:1 com o fundo do gráfico, e cada cor é
# bem diferente da vizinha, inclusive para quem tem daltonismo.
CORES = [
    "#5AA9F0",  # azul
    "#FFA894",  # coral
    "#E86FA8",  # rosa
    "#E8C547",  # amarelo
    "#3FC5D6",  # ciano
    "#F08C3A",  # laranja
    "#C4B0FF",  # lilás
    "#4CC38A",  # verde
    "#DADDE3",  # cinza-claro
    "#86B83A",  # verde-limão
]

sns.set_theme(
    style="darkgrid",
    palette=CORES,
    rc={
        "figure.facecolor": FUNDO_FIGURA,
        "savefig.facecolor": FUNDO_FIGURA,
        "axes.facecolor": FUNDO_GRAFICO,
        "axes.edgecolor": GRADE,
        "axes.labelcolor": TEXTO,
        "axes.titlecolor": TEXTO,
        "axes.titleweight": "bold",
        "grid.color": GRADE,
        "text.color": TEXTO,
        "xtick.color": TEXTO_SECUNDARIO,
        "ytick.color": TEXTO_SECUNDARIO,
        "legend.facecolor": FUNDO_GRAFICO,
        "legend.edgecolor": GRADE,
        "legend.labelcolor": TEXTO,
    },
)


def cores_dos_remetentes(df):
    """Dicionário remetente -> cor. O mesmo remetente tem a mesma cor em todos os gráficos."""
    remetentes = listar_remetentes(df)
    if len(remetentes) <= len(CORES):
        cores = CORES
    else:
        cores = sns.color_palette("husl", len(remetentes))
    return dict(zip(remetentes, cores))


def grafico_historico_remetente(df, remetente=None):
    """R6 - histograma de mensagens por dia.

    Com um remetente: um gráfico só. Com remetente=None: um gráfico por remetente.
    """
    cores = cores_dos_remetentes(df)

    # Uma barra por dia, cobrindo a conversa inteira
    inicio = mdates.date2num(df["data"].min())
    fim = mdates.date2num(df["data"].max() + pd.Timedelta(days=1))

    if remetente is not None:
        mensagens = df[df["remetente"] == remetente]

        fig, ax = plt.subplots(figsize=(11, 4))
        sns.histplot(
            data=mensagens,
            x="data",
            binwidth=1,
            binrange=(inicio, fim),
            color=cores[remetente],
            edgecolor=FUNDO_GRAFICO,
            alpha=1,
            ax=ax,
        )
        ax.set_title(f"Mensagens por dia - {remetente}")
        ax.set_xlabel("Data")
        ax.set_ylabel("Quantidade de mensagens")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        fig.tight_layout()
        return fig

    # Todos os remetentes: small multiples, um embaixo do outro, mesmo eixo X
    remetentes = listar_remetentes(df)
    grade = sns.displot(
        data=df,
        x="data",
        row="remetente",
        row_order=remetentes,
        hue="remetente",
        hue_order=remetentes,
        palette=cores,
        binwidth=1,
        binrange=(inicio, fim),
        edgecolor=FUNDO_GRAFICO,
        alpha=1,
        legend=False,
        height=1.6,
        aspect=7,
        facet_kws={"sharey": False},
    )
    grade.set_titles(row_template="{row_name}")
    grade.set_axis_labels("Data", "Mensagens")
    for ax in grade.axes.flat:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
    plt.setp(grade.axes[-1, 0].get_xticklabels(), rotation=45, ha="right")
    grade.figure.suptitle("Mensagens por dia - todos os remetentes", fontweight="bold")
    grade.figure.tight_layout()
    return grade.figure


def grafico_pizza(df):
    """R7 - percentual de mensagens de cada remetente.

    O seaborn não tem gráfico de pizza, então este usa o matplotlib com o
    mesmo tema e as mesmas cores dos outros gráficos.
    """
    cores = cores_dos_remetentes(df)
    contagem = df["remetente"].value_counts()
    remetentes = listar_remetentes(df)
    contagem = contagem[remetentes]  # do maior para o menor
    total = contagem.sum()

    # Percentual dentro da fatia só se ela tiver pelo menos 3%
    def rotulo_da_fatia(percentual):
        if percentual >= 3:
            return f"{percentual:.1f} %".replace(".", ",")
        return ""

    fig, ax = plt.subplots(figsize=(10, 6))
    fatias, _, textos = ax.pie(
        contagem.values,
        colors=[cores[r] for r in remetentes],
        autopct=rotulo_da_fatia,
        pctdistance=0.78,
        startangle=90,
        counterclock=False,
        wedgeprops={"edgecolor": FUNDO_FIGURA, "linewidth": 2},
    )
    for texto in textos:
        texto.set_color(FUNDO_FIGURA)  # texto escuro sobre as fatias claras
        texto.set_fontweight("bold")

    # Legenda com todos os remetentes: "Nome - 43,6 % (434)"
    legendas = []
    for nome, quantidade in contagem.items():
        percentual = f"{quantidade / total * 100:.1f}".replace(".", ",")
        legendas.append(f"{nome} - {percentual} % ({quantidade})")
    ax.legend(fatias, legendas, title="Remetente", loc="center left", bbox_to_anchor=(1.0, 0.5))

    ax.set_title(f"Percentual de mensagens por remetente (total: {total})")
    ax.axis("equal")
    fig.tight_layout()
    return fig


def grafico_linhas(df, freq="D"):
    """R8 - mensagens ao longo do tempo, uma linha (e uma cor) por remetente.

    freq: "D" (dia), "W" (semana) ou "MS" (mês).
    """
    cores = cores_dos_remetentes(df)
    tabela = mensagens_por_periodo(df, freq)

    # O seaborn prefere o formato "longo": uma linha por (data, remetente)
    longo = tabela.reset_index().melt(id_vars="data", var_name="remetente", value_name="mensagens")

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(
        data=longo,
        x="data",
        y="mensagens",
        hue="remetente",
        hue_order=list(tabela.columns),
        palette=cores,
        linewidth=1.6,
        marker="o" if freq == "MS" else None,
        ax=ax,
    )
    ax.set_title(f"Mensagens ao longo do tempo por remetente (por {FREQUENCIAS[freq].lower()})")
    ax.set_xlabel("Data")
    ax.set_ylabel("Quantidade de mensagens")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.legend(title="Remetente", bbox_to_anchor=(1.01, 1), loc="upper left")
    fig.tight_layout()
    return fig
