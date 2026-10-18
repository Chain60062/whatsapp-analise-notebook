"""Painel interativo (ipywidgets) usado no notebook."""

import html

import ipywidgets as widgets
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import HTML, display

from .analises import historico_remetente, listar_remetentes, resumo_conversas
from .graficos import grafico_historico_remetente, grafico_linhas, grafico_pizza
from .parser import ler_conversa


def descrever_leitura(resultado):
    """Texto com o resumo do arquivo carregado."""
    df = resultado.df

    if resultado.formato == "ios":
        formato = "iPhone"
    else:
        formato = "Android"
    if resultado.dayfirst:
        ordem = "dia/mês"
    else:
        ordem = "mês/dia"

    texto = f"Formato detectado: {formato} (datas em {ordem})\n"
    texto += f"Mensagens: {len(df)}\n"
    texto += f"Remetentes: {df['remetente'].nunique()}\n"
    if len(df) > 0:
        inicio = df["data"].min().strftime("%d/%m/%Y")
        fim = df["data"].max().strftime("%d/%m/%Y")
        texto += f"Período: {inicio} a {fim}\n"
    texto += f"Mensagens do sistema ignoradas: {resultado.mensagens_sistema}"
    return texto


def mostrar_erro(mensagem):
    """Mensagem de erro amigável (sem traceback)."""
    display(HTML(f'<p style="color:#E5484D;font-weight:bold">Erro: {html.escape(mensagem)}</p>'))


def mostrar_figura(fig):
    """Exibe a figura e fecha em seguida, para não acumular figuras abertas."""
    display(fig)
    plt.close(fig)


def tabela_rolavel(df, altura="450px"):
    """Todas as linhas de df numa área com rolagem.

    É HTML simples (e não um widget) para a tabela continuar visível no
    notebook salvo, inclusive no GitHub.
    """
    df = df.copy()
    for coluna in ["remetente", "mensagem"]:
        if coluna in df.columns:
            # Escapa o texto e mostra as quebras de linha da mensagem
            df[coluna] = df[coluna].map(lambda s: html.escape(s).replace("\n", "<br>"))

    tabela = df.to_html(escape=False, border=0)
    return HTML(f'<div style="max-height:{altura};overflow:auto">{tabela}</div>')


def criar_upload(callback):
    """Botão para carregar o .txt. Chama callback(resultado) após ler o arquivo."""
    botao = widgets.FileUpload(accept=".txt", multiple=False, description="Carregar .txt")
    saida = widgets.Output()

    def ao_enviar(mudanca):
        arquivos = mudanca["new"]
        if not arquivos:
            return
        arquivo = arquivos[0]

        saida.clear_output(wait=True)
        with saida:
            try:
                # No ipywidgets 8 o conteúdo vem como memoryview
                resultado = ler_conversa(bytes(arquivo["content"]))
            except ValueError as erro:
                mostrar_erro(f"{arquivo['name']}: {erro}")
                return
            print(f"Arquivo: {arquivo['name']}")
            print(descrever_leitura(resultado))
        callback(resultado)

    botao.observe(ao_enviar, names="value")
    return widgets.VBox([botao, saida])


def criar_painel(df):
    """Painel com as cinco análises (R4 a R8)."""
    remetentes = listar_remetentes(df)

    analise = widgets.ToggleButtons(
        options=["Resumo", "Histórico", "Gráf. histórico", "Pizza", "Linhas"],
        description="Análise:",
    )
    remetente = widgets.Dropdown(options=remetentes, description="Remetente:")
    agrupar = widgets.Dropdown(
        options=[("Dia", "D"), ("Semana", "W"), ("Mês", "MS")],
        description="Agrupar por:",
    )
    executar = widgets.Button(description="Executar", button_style="primary")
    saida = widgets.Output(layout=widgets.Layout(max_height="700px", overflow="auto"))

    def ao_trocar_analise(mudanca=None):
        escolhida = analise.value

        # O gráfico do histórico aceita "Todos"; o histórico em tabela não
        selecionado = remetente.value
        if escolhida == "Gráf. histórico":
            remetente.options = ["Todos"] + remetentes
        else:
            remetente.options = remetentes
        if selecionado in remetente.options:
            remetente.value = selecionado

        # Esconde os controles que não se aplicam
        if escolhida in ["Histórico", "Gráf. histórico"]:
            remetente.layout.display = None
        else:
            remetente.layout.display = "none"
        if escolhida == "Linhas":
            agrupar.layout.display = None
        else:
            agrupar.layout.display = "none"

    def ao_executar(botao):
        saida.clear_output(wait=True)
        with saida:
            try:
                if df.empty:
                    mostrar_erro("A conversa não tem mensagens para analisar.")
                elif analise.value == "Resumo":
                    display(resumo_conversas(df))
                elif analise.value == "Histórico":
                    with pd.option_context("display.max_rows", None):
                        display(historico_remetente(df, remetente.value))
                elif analise.value == "Gráf. histórico":
                    if remetente.value == "Todos":
                        mostrar_figura(grafico_historico_remetente(df))
                    else:
                        mostrar_figura(grafico_historico_remetente(df, remetente.value))
                elif analise.value == "Pizza":
                    mostrar_figura(grafico_pizza(df))
                elif analise.value == "Linhas":
                    mostrar_figura(grafico_linhas(df, agrupar.value))
            except KeyError as erro:
                mostrar_erro(erro.args[0])
            except Exception as erro:
                mostrar_erro(str(erro))

    analise.observe(ao_trocar_analise, names="value")
    executar.on_click(ao_executar)
    ao_trocar_analise()

    return widgets.VBox([analise, remetente, agrupar, executar, saida])
