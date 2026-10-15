"""Painel interativo em ``ipywidgets`` para o notebook."""

from __future__ import annotations

import html
from collections.abc import Callable

import ipywidgets as widgets
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import HTML, display

from .analises import FREQUENCIAS, historico_remetente, listar_remetentes, resumo_conversas
from .graficos import grafico_historico_remetente, grafico_linhas, grafico_pizza
from .parser import ResultadoLeitura, ler_conversa

TODOS = "__todos__"
ANALISES = [
    ("Resumo", "resumo"),
    ("Histórico", "historico"),
    ("Gráf. histórico", "grafico_historico"),
    ("Pizza", "pizza"),
    ("Linhas", "linhas"),
]
_USA_REMETENTE = {"historico", "grafico_historico"}


def descrever_leitura(resultado: ResultadoLeitura) -> str:
    """Resumo em texto do arquivo carregado (formato, totais, período)."""
    df = resultado.df
    nomes = {"ios": "iPhone", "android": "Android"}
    ordem = "dia/mês" if resultado.dayfirst else "mês/dia"
    linhas = [
        f"Formato detectado: {nomes.get(resultado.formato, resultado.formato)} (datas em {ordem})",
        f"Mensagens: {len(df)}",
        f"Remetentes: {df['remetente'].nunique()}",
    ]
    if len(df):
        inicio = df["data"].min().strftime("%d/%m/%Y")
        fim = df["data"].max().strftime("%d/%m/%Y")
        linhas.append(f"Período: {inicio} a {fim}")
    linhas.append(f"Mensagens do sistema ignoradas: {resultado.mensagens_sistema}")
    if resultado.linhas_descartadas:
        linhas.append(f"Linhas antes da 1ª mensagem descartadas: {resultado.linhas_descartadas}")
    return "\n".join(linhas)


def _erro(mensagem: str) -> None:
    display(HTML(f'<div style="color:#b00020;font-weight:bold">⚠️ {html.escape(mensagem)}</div>'))


def mostrar_figura(fig) -> None:
    """Exibe a figura e a fecha, para não acumular figuras abertas."""
    display(fig)
    plt.close(fig)


def tabela_rolavel(df: pd.DataFrame, altura: str = "450px") -> HTML:
    """Todas as linhas de ``df`` numa área de altura fixa com rolagem.

    É HTML puro (e não um ``widgets.Output``) para que a tabela continue
    visível no notebook salvo, inclusive no GitHub/nbviewer, onde widgets não
    são renderizados.
    """
    texto = df.select_dtypes(include="str").columns
    escapado = df.assign(
        **{c: df[c].map(lambda s: html.escape(s).replace("\n", "<br>")) for c in texto}
    )
    tabela = escapado.to_html(max_rows=None, border=0, classes="dataframe", escape=False)
    return HTML(
        f'<div style="max-height:{altura};overflow:auto;border:1px solid #ddd">{tabela}</div>'
    )


def criar_upload(callback: Callable[[ResultadoLeitura], None]) -> widgets.Widget:
    """Botão de upload do ``.txt``; chama ``callback`` com o resultado da leitura."""
    upload = widgets.FileUpload(accept=".txt", multiple=False, description="Carregar .txt")
    status = widgets.Output()

    def ao_enviar(mudanca) -> None:
        arquivos = mudanca["new"]
        if not arquivos:
            return
        arquivo = arquivos[0]
        status.clear_output(wait=True)
        with status:
            try:
                resultado = ler_conversa(bytes(arquivo["content"]))
            except ValueError as exc:
                _erro(f"{arquivo['name']}: {exc}")
                return
            print(f"Arquivo: {arquivo['name']}")
            print(descrever_leitura(resultado))
        callback(resultado)

    upload.observe(ao_enviar, names="value")
    return widgets.VBox([upload, status])


def criar_painel(df: pd.DataFrame) -> widgets.Widget:
    """Painel com as cinco análises (R4–R8)."""
    remetentes = listar_remetentes(df)

    analise = widgets.ToggleButtons(options=ANALISES, value="resumo", description="Análise:")
    remetente = widgets.Dropdown(description="Remetente:")
    freq = widgets.Dropdown(
        options=[(rotulo, chave) for chave, rotulo in FREQUENCIAS.items()],
        value="D",
        description="Agrupar por:",
    )
    executar = widgets.Button(description="Executar", button_style="primary", icon="play")
    saida = widgets.Output(layout=widgets.Layout(max_height="700px", overflow="auto"))

    def atualizar_controles(_=None) -> None:
        escolhida = analise.value
        atual = remetente.value
        opcoes = [(r, r) for r in remetentes]
        if escolhida == "grafico_historico":
            opcoes = [("Todos", TODOS), *opcoes]
        remetente.options = opcoes
        valores = [v for _, v in opcoes]
        if atual in valores:
            remetente.value = atual
        elif valores:
            remetente.value = valores[0]
        remetente.layout.display = None if escolhida in _USA_REMETENTE else "none"
        freq.layout.display = None if escolhida == "linhas" else "none"

    def rodar(_=None) -> None:
        saida.clear_output(wait=True)
        with saida:
            try:
                escolhida = analise.value
                if df.empty:
                    _erro("A conversa não tem mensagens para analisar.")
                elif escolhida == "resumo":
                    display(resumo_conversas(df))
                elif escolhida == "historico":
                    with pd.option_context("display.max_rows", None):
                        display(historico_remetente(df, remetente.value))
                elif escolhida == "grafico_historico":
                    nome = None if remetente.value == TODOS else remetente.value
                    mostrar_figura(grafico_historico_remetente(df, nome))
                elif escolhida == "pizza":
                    mostrar_figura(grafico_pizza(df))
                elif escolhida == "linhas":
                    mostrar_figura(grafico_linhas(df, freq.value))
            except KeyError as exc:
                _erro(str(exc.args[0]) if exc.args else str(exc))
            except Exception as exc:  # o painel não deve mostrar traceback
                _erro(f"Não foi possível executar a análise: {exc}")

    analise.observe(atualizar_controles, names="value")
    executar.on_click(rodar)
    atualizar_controles()

    return widgets.VBox([analise, remetente, freq, executar, saida])
