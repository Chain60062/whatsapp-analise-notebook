import pandas as pd
import pytest

from whatsapp_analise import (
    historico_remetente,
    ler_conversa,
    listar_remetentes,
    mensagens_por_dia,
    mensagens_por_periodo,
    resumo_conversas,
)

AVISO = (
    "As mensagens e as ligações são protegidas com a criptografia de ponta a ponta "
    "e ficam somente entre você e os participantes desta conversa."
)


def ler(texto: str, **kwargs):
    return ler_conversa(texto.encode("utf-8"), **kwargs)


def test_ios_basico():
    r = ler("[9/29/25, 6:08:52 PM] Beto: Entrou um cara no ônibus\n")
    assert r.formato == "ios"
    assert r.dayfirst is False
    linha = r.df.iloc[0]
    assert linha["data"] == pd.Timestamp("2025-09-29")
    assert linha["hora"] == "18:08:52"
    assert linha["remetente"] == "Beto"
    assert linha["mensagem"] == "Entrou um cara no ônibus"
    assert list(r.df.columns) == ["data", "hora", "remetente", "mensagem"]


def test_ios_meia_noite_e_meio_dia():
    r = ler("[9/29/25, 12:41:32 PM] A: x\n[9/30/25, 12:05:00 AM] A: y\n")
    assert r.df["hora"].tolist() == ["12:41:32", "00:05:00"]


def test_android_basico():
    r = ler("29/09/2025 12:41 - Fulano: vcs viram essa\n")
    assert r.formato == "android"
    assert r.dayfirst is True
    linha = r.df.iloc[0]
    assert linha["data"] == pd.Timestamp("2025-09-29")
    assert linha["hora"] == "12:41"
    assert linha["remetente"] == "Fulano"
    assert linha["mensagem"] == "vcs viram essa"


def test_android_sistema_sem_remetente():
    r = ler("29/09/2025 12:40 - Fulano adicionou Fulano\n29/09/2025 12:41 - Fulano: oi\n")
    assert len(r.df) == 1
    assert r.mensagens_sistema == 1


def test_multilinha():
    texto = (
        "[10/7/25, 12:13:39 PM] Ana: *CHURRAS*\n"
        " \n"
        "- DIA 17\n"
        "- BETO NO VOLANTE\n"
        "[10/7/25, 12:14:21 PM] Bia: Enquete: CHURAS\n"
        "    - VOU\n"
        "    - NAO VOU\n"
    )
    r = ler(texto)
    assert len(r.df) == 2
    assert r.df.loc[0, "mensagem"] == "*CHURRAS*\n \n- DIA 17\n- BETO NO VOLANTE"
    assert r.df.loc[1, "mensagem"] == "Enquete: CHURAS\n    - VOU\n    - NAO VOU"


def test_multilinha_android_com_traco():
    texto = "07/10/2025 12:13 - Ana: lista\n- DIA 17\n- item 2\n"
    r = ler(texto)
    assert len(r.df) == 1
    assert r.df.loc[0, "mensagem"] == "lista\n- DIA 17\n- item 2"


def test_espacos_no_fim_removidos():
    r = ler("[9/29/25, 6:50:18 PM] A: link\n\nTá enviando   \n \n")
    assert r.df.loc[0, "mensagem"] == "link\n\nTá enviando"


def test_sistema_ignorado():
    r = ler("[9/12/25, 6:43:21 PM] - [Ligação]\n[9/29/25, 6:08:52 PM] A: oi\n")
    assert len(r.df) == 1
    assert r.mensagens_sistema == 1
    assert "[Ligação]" not in r.df["mensagem"].tolist()


def test_aviso_criptografia_descartado():
    r = ler(AVISO + "\n[9/29/25, 6:08:52 PM] A: oi\n")
    assert len(r.df) == 1
    assert r.linhas_descartadas == 1
    assert not r.df["mensagem"].str.contains("criptografia").any()


def test_caracteres_invisiveis():
    texto = "﻿[9/29/25, 6:08:52 PM] ‎Ana: oi tudo bem‏\n"
    r = ler(texto)
    assert len(r.df) == 1
    assert r.df.loc[0, "hora"] == "18:08:52"
    assert r.df.loc[0, "remetente"] == "Ana"
    assert r.df.loc[0, "mensagem"] == "oi tudo bem"


def test_ampm_com_pontos():
    r = ler("[9/29/25, 6:08:52 p. m.] Ana: oi\n")
    assert r.df.loc[0, "hora"] == "18:08:52"


def test_dois_pontos_na_mensagem():
    r = ler("[9/29/25, 6:08:52 PM] Fulano: hora: 10:00\n")
    assert r.df.loc[0, "remetente"] == "Fulano"
    assert r.df.loc[0, "mensagem"] == "hora: 10:00"


def test_midia_e_apagada_mantidas():
    r = ler(
        "[9/29/25, 6:00:00 PM] A: <figurinha omitida>\n"
        "[9/29/25, 6:00:01 PM] Você: Mensagem apagada\n"
        "[9/29/25, 6:00:02 PM] +55 00 0000-0001: [Encaminhada] https://x\n"
    )
    assert r.df["remetente"].tolist() == ["A", "Você", "+55 00 0000-0001"]
    assert len(r.df) == 3


def test_deteccao_dayfirst():
    assert ler("13/01/2025 10:00 - A: oi\n").dayfirst is True
    assert ler("[1/13/25, 10:00:00 AM] A: oi\n").dayfirst is False
    # Sem evidência numérica: AM/PM → mês/dia; 24 h → dia/mês.
    assert ler("[1/2/25, 10:00:00 AM] A: oi\n").dayfirst is False
    assert ler("01/02/2025 10:00 - A: oi\n").dayfirst is True


def test_dayfirst_forcado():
    r = ler("01/02/2025 10:00 - A: oi\n", dayfirst=False)
    assert r.df.loc[0, "data"] == pd.Timestamp("2025-01-02")


def test_ordenacao_estavel():
    r = ler(
        "[9/30/25, 1:00:00 PM] A: depois\n"
        "[9/29/25, 1:00:00 PM] B: primeira\n"
        "[9/29/25, 1:00:00 PM] C: segunda\n"
    )
    assert r.df["mensagem"].tolist() == ["primeira", "segunda", "depois"]
    assert isinstance(r.df.index, pd.RangeIndex)


def test_arquivo_invalido():
    with pytest.raises(ValueError, match="não reconhecido"):
        ler("Isto não é uma conversa.\nNem isto.\n")


def test_leitura_por_caminho_e_latin1(tmp_path):
    arquivo = tmp_path / "conversa.txt"
    arquivo.write_bytes("29/09/2025 12:41 - José: ação\n".encode("latin-1"))
    r = ler_conversa(arquivo)
    assert r.df.loc[0, "remetente"] == "José"
    assert r.df.loc[0, "mensagem"] == "ação"


# --- análises ---------------------------------------------------------------

@pytest.fixture
def df():
    return ler(
        "[9/1/25, 10:00:00 AM] Ana: a\n"
        "[9/1/25, 10:01:00 AM] Bia: b\n"
        "[9/1/25, 10:02:00 AM] Ana: c\n"
        "[9/4/25, 10:00:00 AM] Ana: d\n"
        "[9/4/25, 10:00:00 AM] Caio: e\n"
        "[9/4/25, 11:00:00 AM] Bia: f\n"
    ).df


def test_resumo_ordenado(df):
    resumo = resumo_conversas(df)
    assert resumo["remetente"].tolist() == ["Ana", "Bia", "Caio"]
    assert resumo["total_mensagens"].is_monotonic_decreasing
    assert resumo["percentual"].sum() == pytest.approx(100, abs=0.5)
    assert resumo.index.tolist() == [1, 2, 3]


def test_resumo_nao_altera_entrada(df):
    copia = df.copy()
    resumo_conversas(df)
    historico_remetente(df, "Ana")
    pd.testing.assert_frame_equal(df, copia)


def test_listar_remetentes(df):
    assert listar_remetentes(df) == ["Ana", "Bia", "Caio"]


def test_historico_remetente(df):
    hist = historico_remetente(df, "Ana")
    assert list(hist.columns) == ["data", "hora", "mensagem"]
    assert hist["mensagem"].tolist() == ["a", "c", "d"]


def test_historico_remetente_inexistente(df):
    with pytest.raises(KeyError, match="Zé"):
        historico_remetente(df, "Zé")


def test_mensagens_por_dia_preenche_zeros(df):
    serie = mensagens_por_dia(df)
    assert serie.tolist() == [3, 0, 0, 3]
    assert serie.index[1] == pd.Timestamp("2025-09-02")
    caio = mensagens_por_dia(df, "Caio")
    assert caio.tolist() == [0, 0, 0, 1]


def test_mensagens_por_periodo(df):
    tabela = mensagens_por_periodo(df, "D")
    assert list(tabela.columns) == ["Ana", "Bia", "Caio"]
    assert tabela.shape == (4, 3)
    assert tabela.loc["2025-09-02"].sum() == 0
    assert tabela.to_numpy().sum() == len(df)
    for freq in ("W", "MS"):
        assert mensagens_por_periodo(df, freq).to_numpy().sum() == len(df)
    with pytest.raises(ValueError):
        mensagens_por_periodo(df, "H")
