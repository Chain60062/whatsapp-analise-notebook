import matplotlib

matplotlib.use("Agg")  # sem janela, só para testar

import matplotlib.pyplot as plt
import pytest
from matplotlib.figure import Figure

from whatsapp_analise import ler_conversa
from whatsapp_analise.graficos import (
    CORES,
    cores_dos_remetentes,
    grafico_historico_remetente,
    grafico_linhas,
    grafico_pizza,
)


@pytest.fixture
def df():
    return ler_conversa(
        b"[9/1/25, 10:00:00 AM] Ana: a\n"
        b"[9/1/25, 10:01:00 AM] Bia: b\n"
        b"[9/1/25, 10:02:00 AM] Ana: c\n"
        b"[9/4/25, 10:00:00 AM] Ana: d\n"
        b"[10/2/25, 10:00:00 AM] Caio: e\n"
    ).df


def test_cores_fixas_por_remetente(df):
    cores = cores_dos_remetentes(df)
    assert cores == {"Ana": CORES[0], "Bia": CORES[1], "Caio": CORES[2]}


def test_historico_um_remetente(df):
    fig = grafico_historico_remetente(df, "Ana")
    assert isinstance(fig, Figure)
    # Uma barra por dia, de 01/09 a 02/10 (32 dias), e 3 mensagens no total
    barras = fig.axes[0].patches
    assert len(barras) == 32
    assert sum(b.get_height() for b in barras) == 3
    plt.close(fig)


def test_historico_todos(df):
    fig = grafico_historico_remetente(df)
    assert len(fig.axes) == 3
    plt.close(fig)


def test_pizza(df):
    fig = grafico_pizza(df)
    legenda = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
    assert legenda[0] == "Ana - 60,0 % (3)"
    assert len(legenda) == 3
    plt.close(fig)


@pytest.mark.parametrize("freq", ["D", "W", "MS"])
def test_linhas(df, freq):
    fig = grafico_linhas(df, freq)
    legenda = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
    assert legenda == ["Ana", "Bia", "Caio"]
    plt.close(fig)
