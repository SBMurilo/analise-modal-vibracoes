# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: config
# -----------------------------------------------------------------------------
# Constantes globais do aplicativo:
#   PASTA_GRAFICOS — pasta em disco onde os PNGs exportados são salvos. Edite
#                    este caminho antes de rodar se quiser gravar em outro
#                    lugar. A pasta é criada automaticamente se não existir.
#   NOME_BASE      — título do app usado no cabeçalho da tela do diagrama
#                    (junto com o título dado pelo usuário) e na janela do
#                    pywebview.
#   FIG_HEIGHT     — altura fixa (em px) do gráfico Plotly na tela do diagrama;
#                    também usada no cálculo do posicionamento das plaquinhas
#                    RPM em figure.py.
# =============================================================================

import pathlib

PASTA_GRAFICOS = pathlib.Path(r"C:\CAMINHO\PARA\SUA\PASTA\Graficos")  # <-- ALTERE para a sua pasta
PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)

NOME_BASE  = "Diagrama de Frequências Naturais X Excitações"
FIG_HEIGHT = 820
