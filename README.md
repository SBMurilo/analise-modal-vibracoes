# Análise Modal e Vibrações

Duas ferramentas interativas em Python (Dash + Plotly) para **análise de resultados modais** de equipamentos rotativos: uma para avaliar o risco de ressonância contra a velocidade de operação e outra para entender a participação de cada modo na resposta.

## 1. Diagrama de Frequências Naturais × Excitações (`diagrama-campbell/`)

Gera um **diagrama de Campbell** a partir das frequências naturais obtidas em uma análise modal.

- Entrada: conjuntos de frequências naturais (modos), faixa de rotação de operação (Nmin–Nmax), harmônicas de excitação (1×, 2×...) e, opcionalmente, a massa efetiva modal (MPF) de cada modo em X, Y e Z.
- Calcula os **pontos de cruzamento** entre as harmônicas e os modos, e o **RPM crítico** de cada um.
- Marca a **zona de operação** (com tolerância configurável) e destaca em vermelho os cruzamentos perigosos, em verde os seguros e os modos com MPF acima do limiar.
- Legenda dinâmica, filtros por modo/ponto, tabelas de cruzamento e de MPF abaixo do gráfico.
- Exporta o gráfico em **PNG** (alta resolução) e os dados em **Excel**.
- Interface em **português, inglês e espanhol**; roda em janela própria (pywebview) ou no navegador.

O código é modular (`layout`, `callbacks_*`, `figure`, `compute`, `tables`...), com controle de revisões no cabeçalho de cada arquivo.

```bash
cd diagrama-campbell
python main.py
```

Antes de rodar, ajuste `PASTA_GRAFICOS` em `config.py` (pasta onde os PNGs são salvos).

## 2. Explorador de Análise Modal (`explorador-modal/`)

Aplicativo didático de arquivo único que mostra, por direção (X, Y, Z):

- **Massa efetiva modal** por modo, com o critério dos 90% de massa acumulada;
- **Fator de amplificação dinâmica (DAF = 1/2ζ)** em função do amortecimento;
- **Classificação de risco** (alto/médio/baixo) combinando massa efetiva e DAF.

Baseado em Irvine (2012) e Chopra (2001). Os dados de exemplo ficam no topo do arquivo (`MODOS`) e devem ser substituídos pelos resultados reais.

```bash
cd explorador-modal
python explorador_modal.py
```

## Instalação

Python 3.13 (testado).

```bash
pip install -r requirements.txt
```

## Tecnologias

Python, Dash, Plotly, NumPy, pandas, openpyxl, Kaleido, pywebview.
