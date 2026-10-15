# Análise de Dados de Conversas do WhatsApp

Trabalho de Data Science (A2). Notebook Jupyter que lê a exportação `.txt` de um grupo do WhatsApp, monta um `pandas.DataFrame` com **data**, **hora**, **remetente** e **mensagem** e oferece cinco análises: um resumo por remetente, o histórico de um remetente e três gráficos (histórico por dia, pizza e linhas).

**Integrantes:**
- Integrante 1
- Integrante 2

## Requisitos

- **Python 3.14** (3.12 e 3.13 também funcionam; o mínimo é 3.12 por causa do NumPy 2.5).
- Dependências fixadas em [`requirements.txt`](requirements.txt): pandas 3.0.6, matplotlib 3.11.2, ipywidgets 8.1.9, jupyterlab 4.6.4 e ipykernel 7.4.0. O pytest 9.1.1 fica em [`requirements-dev.txt`](requirements-dev.txt).

## Instalação

### Com `venv` (Windows)

```bash
py -3.14 -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
pip install -r requirements-dev.txt
```

No Linux/macOS, use `python3.14 -m venv .venv` e `source .venv/bin/activate`.

### Com conda

```bash
conda create -n whatsapp-analise python=3.14
```

```bash
conda activate whatsapp-analise
```

```bash
pip install -r requirements-dev.txt
```

## Como rodar

```bash
jupyter lab
```

Abra [`analise_whatsapp.ipynb`](analise_whatsapp.ipynb) e use **Run → Run All Cells**. Por padrão o notebook lê [`dados/exemplo_anonimizado.txt`](dados/exemplo_anonimizado.txt). Para analisar outra conversa:

- clique em **Carregar .txt** (seção 1) e escolha o arquivo: a tabela e o painel interativo são atualizados; ou
- troque a variável `CAMINHO` e rode tudo de novo (atualiza também as seções 4 a 8).

O notebook está salvo **com as saídas**, então dá para ver os resultados no GitHub sem executar nada. O painel interativo (ipywidgets) só aparece com um kernel rodando.

Para rodar os testes:

```bash
pytest
```

## Como exportar a conversa do WhatsApp

- **Android:** abra o grupo → menu **⋮** → **Mais** → **Exportar conversa** → **Sem mídia**.
- **iPhone:** abra o grupo → toque no nome do grupo → **Exportar conversa** → **Sem mídia**. O iPhone gera um `.zip`; extraia o `_chat.txt` de dentro dele.

O leitor aceita os dois formatos (iPhone `[M/D/AA, H:MM:SS PM] Nome: texto` e Android `DD/MM/AAAA HH:MM - Nome: texto`) e descobre sozinho se a data está em dia/mês ou mês/dia.

> ⚠️ **Privacidade:** a conversa real tem números de telefone e conteúdo pessoal. Não versione o `.txt` real. O `.gitignore` já ignora `dados/*.txt`, com exceção do exemplo anonimizado.

## O que o notebook faz

| Requisito | Onde |
|-----------|------|
| R1/R2 — ler o `.txt` e montar o DataFrame | `whatsapp_analise/parser.py` (`ler_conversa`) |
| R3 — tabela completa | Seção 2 do notebook |
| R4 — resumo das conversas | `resumo_conversas` (seção 4 e painel) |
| R5 — histórico do remetente | `historico_remetente` (seção 5 e painel) |
| R6 — gráfico do histórico | `grafico_historico_remetente` (seção 6 e painel) |
| R7 — gráfico de pizza | `grafico_pizza` (seção 7 e painel) |
| R8 — gráfico de linhas | `grafico_linhas` (seção 8 e painel) |

Regras de leitura:

- Cada mensagem com data, hora e remetente conta como uma "conversa".
- Mensagens do sistema (ligações, notificações, avisos de criptografia, eventos sem remetente) ficam fora do DataFrame; o total ignorado aparece ao carregar o arquivo.
- Mídias omitidas (`<imagem ocultada>`, `<figurinha omitida>`…) e `Mensagem apagada` contam como mensagens.
- Mensagens com várias linhas (incluindo enquetes) viram um registro só, com as linhas separadas por `\n`.

## Estrutura

```text
whatsapp-analise/
├── analise_whatsapp.ipynb       # notebook principal (entregável)
├── whatsapp_analise/
│   ├── parser.py                # .txt -> DataFrame
│   ├── analises.py              # tabelas (R4, R5) e contagens por período
│   ├── graficos.py              # gráficos matplotlib (R6, R7, R8)
│   └── interface.py             # painel ipywidgets
├── dados/exemplo_anonimizado.txt
├── docs/img/                    # prints dos gráficos usados neste README
└── tests/test_parser.py
```

## Gráficos (conversa de exemplo)

O exemplo foi gerado a partir de uma conversa real: os horários e a quantidade de mensagens de cada pessoa foram mantidos, mas os nomes, os números e todo o texto das mensagens foram trocados.

**R6 — mensagens por dia de um remetente**

![Mensagens por dia de um remetente](docs/img/historico_remetente.png)

**R6 — mensagens por dia, todos os remetentes**

![Mensagens por dia de todos os remetentes](docs/img/historico_todos.png)

**R7 — percentual de mensagens por remetente**

![Gráfico de pizza](docs/img/pizza.png)

**R8 — mensagens ao longo do tempo (por dia e por mês)**

![Gráfico de linhas por dia](docs/img/linhas_dia.png)

![Gráfico de linhas por mês](docs/img/linhas_mes.png)
