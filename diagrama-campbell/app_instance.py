# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: app_instance
# -----------------------------------------------------------------------------
# Cria e exporta a instância ÚNICA do Dash usada por todo o app.
#   • É importada por layout.py (que define app.layout) e por cada
#     callbacks_*.py (que registram callbacks via @callback e
#     app.clientside_callback).
#   • suppress_callback_exceptions=True permite que callbacks referenciem IDs
#     que ainda não existem no momento do registro — necessário porque a tela
#     do diagrama só é renderizada dinamicamente depois de "Gerar Diagrama"
#     (os botões de zona, checklist de modos, botões Excel etc. são criados
#     em tempo de execução por render_dynamic_controls em callbacks_setup).
# =============================================================================

from dash import Dash

app = Dash(__name__, suppress_callback_exceptions=True)
