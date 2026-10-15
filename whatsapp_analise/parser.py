"""Leitura da exportação ``.txt`` do WhatsApp para um ``pandas.DataFrame``."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

RE_IOS = re.compile(
    r"^\[(?P<data>\d{1,2}/\d{1,2}/\d{2,4}),\s*"
    r"(?P<hora>\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap]\.?\s?[Mm]\.?)?)\]\s"
    r"(?P<resto>.*)$"
)
RE_ANDROID = re.compile(
    r"^(?P<data>\d{1,2}/\d{1,2}/\d{2,4}),?\s"
    r"(?P<hora>\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap]\.?\s?[Mm]\.?)?)\s-\s"
    r"(?P<resto>.*)$"
)
RE_REMETENTE = re.compile(r"^(?P<remetente>[^:]+?):\s(?P<mensagem>.*)$", re.DOTALL)
RE_AMPM = re.compile(r"\s?([APap])\.?\s?[Mm]\.?$")

# Caracteres invisíveis que algumas exportações inserem.
_REMOVER = dict.fromkeys(map(ord, "‎‏﻿"))
_TROCAR_POR_ESPACO = dict.fromkeys(map(ord, "  "), " ")
_TABELA_NORMALIZACAO = {**_REMOVER, **_TROCAR_POR_ESPACO}

COLUNAS = ["data", "hora", "remetente", "mensagem"]


@dataclass
class ResultadoLeitura:
    df: pd.DataFrame  # 4 colunas: data, hora, remetente, mensagem
    formato: str  # "ios" | "android"
    dayfirst: bool
    mensagens_sistema: int  # quantas foram descartadas
    linhas_descartadas: int  # texto antes da 1ª mensagem


def _ler_texto(origem: str | Path | bytes) -> str:
    if isinstance(origem, (bytes, bytearray, memoryview)):
        dados = bytes(origem)
    else:
        dados = Path(origem).read_bytes()
    try:
        return dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        return dados.decode("latin-1")


def _normalizar(texto: str) -> str:
    return texto.translate(_TABELA_NORMALIZACAO)


def _detectar_dayfirst(datas: list[str], tem_ampm: bool) -> bool:
    campos = [d.split("/") for d in datas]
    if any(int(c[0]) > 12 for c in campos):
        return True
    if any(int(c[1]) > 12 for c in campos):
        return False
    return not tem_ampm


def _padronizar_hora(hora: str) -> str:
    """``6:08:52 p.m.`` -> ``6:08:52 PM``."""
    hora = hora.strip()
    m = RE_AMPM.search(hora)
    if m:
        hora = hora[: m.start()].strip() + f" {m.group(1).upper()}M"
    return hora


def _formato_datahora(
    datas: pd.Series, horas: pd.Series, dayfirst: bool
) -> tuple[str, bool]:
    """Formato explícito para ``pd.to_datetime`` e se a hora tem segundos."""
    ano = "%Y" if len(datas.iloc[0].split("/")[2]) == 4 else "%y"
    fmt_data = f"%d/%m/{ano}" if dayfirst else f"%m/%d/{ano}"
    tem_segundos = horas.iloc[0].split(" ")[0].count(":") == 2
    tem_ampm = horas.iloc[0].endswith("M")
    if tem_ampm:
        fmt_hora = "%I:%M:%S %p" if tem_segundos else "%I:%M %p"
    else:
        fmt_hora = "%H:%M:%S" if tem_segundos else "%H:%M"
    return f"{fmt_data} {fmt_hora}", tem_segundos


def ler_conversa(
    origem: str | Path | bytes, dayfirst: bool | None = None
) -> ResultadoLeitura:
    """Lê uma exportação ``.txt`` do WhatsApp (iPhone ou Android, sem mídia).

    ``origem`` pode ser um caminho ou os ``bytes`` do arquivo. ``dayfirst``
    força a ordem dia/mês; se ``None``, é detectada a partir das datas.
    """
    linhas = _normalizar(_ler_texto(origem)).splitlines()

    registros: list[dict[str, str]] = []
    formato: str | None = None
    linhas_descartadas = 0

    for linha in linhas:
        m = None
        if formato in (None, "ios"):
            m = RE_IOS.match(linha)
            if m and formato is None:
                formato = "ios"
        if m is None and formato in (None, "android"):
            m = RE_ANDROID.match(linha)
            if m and formato is None:
                formato = "android"

        if m:
            registros.append(m.groupdict())
        elif registros:
            registros[-1]["resto"] += "\n" + linha
        else:
            linhas_descartadas += 1

    if not registros:
        raise ValueError("Arquivo não reconhecido como exportação do WhatsApp")

    mensagens: list[dict[str, str]] = []
    mensagens_sistema = 0
    for reg in registros:
        resto = reg["resto"]
        m = None if resto.startswith("- ") else RE_REMETENTE.match(resto)
        if m is None:
            mensagens_sistema += 1
            continue
        mensagens.append(
            {
                "data": reg["data"],
                "hora": _padronizar_hora(reg["hora"]),
                "remetente": m.group("remetente").strip(),
                "mensagem": m.group("mensagem").rstrip(),
            }
        )

    if dayfirst is None:
        todas_datas = [r["data"] for r in registros]
        tem_ampm = bool(RE_AMPM.search(registros[0]["hora"]))
        dayfirst = _detectar_dayfirst(todas_datas, tem_ampm)

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

    bruto = pd.DataFrame(mensagens)
    fmt, tem_segundos = _formato_datahora(bruto["data"], bruto["hora"], dayfirst)
    instante = pd.to_datetime(bruto["data"] + " " + bruto["hora"], format=fmt)

    df = (
        pd.DataFrame(
            {
                "data": instante.dt.normalize(),
                "hora": instante.dt.strftime("%H:%M:%S" if tem_segundos else "%H:%M"),
                "remetente": bruto["remetente"].astype("str"),
                "mensagem": bruto["mensagem"].astype("str"),
                "_instante": instante,
            }
        )
        .sort_values("_instante", kind="stable")
        .drop(columns="_instante")
        .reset_index(drop=True)
    )

    return ResultadoLeitura(
        df=df[COLUNAS],
        formato=formato,
        dayfirst=dayfirst,
        mensagens_sistema=mensagens_sistema,
        linhas_descartadas=linhas_descartadas,
    )
