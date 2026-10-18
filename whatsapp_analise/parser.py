"""Leitura da exportação .txt do WhatsApp para um pandas.DataFrame."""

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Início de mensagem no iPhone: [9/29/25, 6:08:52 PM] resto
RE_IOS = re.compile(
    r"^\[(?P<data>\d{1,2}/\d{1,2}/\d{2,4}),\s*"
    r"(?P<hora>\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap]\.?\s?[Mm]\.?)?)\]\s"
    r"(?P<resto>.*)$"
)

# Início de mensagem no Android: 29/09/2025 18:08 - resto
RE_ANDROID = re.compile(
    r"^(?P<data>\d{1,2}/\d{1,2}/\d{2,4}),?\s"
    r"(?P<hora>\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap]\.?\s?[Mm]\.?)?)\s-\s"
    r"(?P<resto>.*)$"
)

# "Remetente: mensagem" (divide no primeiro ": ")
RE_REMETENTE = re.compile(r"^(?P<remetente>[^:]+?):\s(?P<mensagem>.*)$", re.DOTALL)

# AM/PM no fim da hora, em qualquer grafia: "PM", "pm", "p.m.", "p. m."
RE_AMPM = re.compile(r"\s?([APap])\.?\s?[Mm]\.?$")


@dataclass
class ResultadoLeitura:
    df: pd.DataFrame  # colunas: data, hora, remetente, mensagem
    formato: str  # "ios" ou "android"
    dayfirst: bool  # True = dia/mês, False = mês/dia
    mensagens_sistema: int  # mensagens sem remetente que foram descartadas
    linhas_descartadas: int  # texto antes da primeira mensagem


def ler_conversa(origem, dayfirst=None):
    """Lê uma exportação .txt do WhatsApp (iPhone ou Android, sem mídia).

    origem: caminho do arquivo ou os bytes do arquivo (vindos do upload).
    dayfirst: força a ordem da data (True = dia/mês). Se None, é detectada.
    """
    # 1. Ler o arquivo (utf-8-sig remove o BOM; latin-1 é o plano B)
    if isinstance(origem, (bytes, bytearray, memoryview)):
        dados = bytes(origem)
    else:
        dados = Path(origem).read_bytes()
    try:
        texto = dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = dados.decode("latin-1")

    # 2. Remover caracteres invisíveis e trocar espaços especiais por espaço comum
    texto = texto.replace("‎", "").replace("‏", "").replace("﻿", "")
    texto = texto.replace(" ", " ").replace(" ", " ")

    # 3. Juntar as linhas em mensagens. Uma linha que não começa com data/hora
    #    continua a mensagem anterior.
    registros = []
    formato = None
    linhas_descartadas = 0

    for linha in texto.splitlines():
        encontrado = None
        if formato in (None, "ios"):
            encontrado = RE_IOS.match(linha)
            if encontrado and formato is None:
                formato = "ios"
        if encontrado is None and formato in (None, "android"):
            encontrado = RE_ANDROID.match(linha)
            if encontrado and formato is None:
                formato = "android"

        if encontrado:
            registros.append(encontrado.groupdict())
        elif registros:
            registros[-1]["resto"] += "\n" + linha
        else:
            linhas_descartadas += 1  # cabeçalho ou aviso de criptografia

    if not registros:
        raise ValueError("Arquivo não reconhecido como exportação do WhatsApp")

    # 4. Separar remetente e mensagem. Sem remetente = mensagem do sistema.
    mensagens = []
    mensagens_sistema = 0
    for registro in registros:
        resto = registro["resto"]
        encontrado = RE_REMETENTE.match(resto)
        if resto.startswith("- ") or encontrado is None:
            mensagens_sistema += 1
            continue

        # Padroniza AM/PM: "6:08:52 p. m." -> "6:08:52 PM"
        hora = registro["hora"].strip()
        ampm = RE_AMPM.search(hora)
        if ampm:
            hora = hora[: ampm.start()].strip() + " " + ampm.group(1).upper() + "M"

        mensagens.append(
            {
                "data": registro["data"],
                "hora": hora,
                "remetente": encontrado.group("remetente").strip(),
                "mensagem": encontrado.group("mensagem").rstrip(),
            }
        )

    # 5. Descobrir se a data é dia/mês ou mês/dia olhando todas as datas
    tem_ampm = RE_AMPM.search(registros[0]["hora"]) is not None
    if dayfirst is None:
        primeiros = [int(r["data"].split("/")[0]) for r in registros]
        segundos = [int(r["data"].split("/")[1]) for r in registros]
        if max(primeiros) > 12:
            dayfirst = True
        elif max(segundos) > 12:
            dayfirst = False
        else:
            dayfirst = not tem_ampm  # AM/PM é padrão americano (mês/dia)

    if not mensagens:
        df = pd.DataFrame(
            {
                "data": pd.Series(dtype="datetime64[ns]"),
                "hora": pd.Series(dtype="str"),
                "remetente": pd.Series(dtype="str"),
                "mensagem": pd.Series(dtype="str"),
            }
        )
        return ResultadoLeitura(df, formato, dayfirst, mensagens_sistema, linhas_descartadas)

    # 6. Converter data e hora com um formato explícito
    df = pd.DataFrame(mensagens)

    ano_com_4_digitos = len(df.loc[0, "data"].split("/")[2]) == 4
    ano = "%Y" if ano_com_4_digitos else "%y"
    if dayfirst:
        formato_data = f"%d/%m/{ano}"
    else:
        formato_data = f"%m/%d/{ano}"

    tem_segundos = df.loc[0, "hora"].count(":") == 2
    if tem_ampm and tem_segundos:
        formato_hora = "%I:%M:%S %p"
    elif tem_ampm:
        formato_hora = "%I:%M %p"
    elif tem_segundos:
        formato_hora = "%H:%M:%S"
    else:
        formato_hora = "%H:%M"

    data_hora = pd.to_datetime(
        df["data"] + " " + df["hora"], format=f"{formato_data} {formato_hora}"
    )

    # 7. Montar o DataFrame final em ordem cronológica
    df["data"] = data_hora.dt.normalize()
    df["hora"] = data_hora.dt.strftime("%H:%M:%S" if tem_segundos else "%H:%M")
    df["data_hora"] = data_hora
    df = df.sort_values("data_hora", kind="stable").reset_index(drop=True)
    df = df[["data", "hora", "remetente", "mensagem"]]

    return ResultadoLeitura(df, formato, dayfirst, mensagens_sistema, linhas_descartadas)
