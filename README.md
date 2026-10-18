# Análise de Dados de Conversas do WhatsApp

Notebook Jupyter que lê a exportação `.txt` de um grupo do WhatsApp, monta um `pandas.DataFrame` com **data**, **hora**, **remetente** e **mensagem** e oferece cinco análises: um resumo por remetente, o histórico de um remetente e três gráficos (histórico por dia, pizza e linhas).

**Integrantes:**
- Vinícius
- Nicollas

## Requisitos

- **Python 3.14** (3.12 e 3.13 também funcionam; o mínimo é 3.12 por causa do NumPy 2.5).
- Dependências fixadas em [`requirements.txt`](requirements.txt): pandas, matplotlib, seaborn, ipywidgets, jupyterlab e ipykernel. O pytest fica em [`requirements-dev.txt`](requirements-dev.txt).

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

Abra [`analise_whatsapp.ipynb`](analise_whatsapp.ipynb) e use **Run → Run All Cells**. Por padrão o notebook lê [`dados/chat_exemplo.txt`](dados/chat_exemplo.txt), uma conversa fictícia de cerca de 1000 mensagens no mesmo formato da exportação do iPhone, com nomes inventados e números de telefone com DDD 00, que não existe. Para analisar outra conversa:

- clique em **Carregar .txt** (seção 1) e escolha o arquivo: todas as seções são atualizadas; ou
- coloque a exportação em `dados/` (por exemplo `dados/chat.txt`, que o `.gitignore` não deixa versionar), troque a variável `CAMINHO` e rode tudo de novo.

O remetente do histórico (seção 5) e do gráfico do histórico (seção 6) e o agrupamento do gráfico de linhas (seção 8) são escolhidos em listas, sem alterar código.

O notebook está salvo **com as saídas** da conversa fictícia, então dá para ver os resultados no GitHub sem executar nada (com a opção padrão de cada lista). As listas e o painel interativo (ipywidgets) só funcionam com um kernel rodando.

Os gráficos usam o seaborn com um tema escuro próprio (fundo grafite e 10 cores claras, uma por remetente). O gráfico de pizza é feito com o matplotlib, porque o seaborn não tem pizza, mas usa o mesmo tema e as mesmas cores. Nele, os remetentes com menos mensagens (somando até 10 % do total) ficam juntos numa fatia "Outros"; a legenda continua mostrando o percentual exato de cada remetente. As tabelas seguem o tema do JupyterLab: para deixar tudo escuro, use **Settings → Theme → JupyterLab Dark**.

Para rodar os testes:

```bash
pytest
```