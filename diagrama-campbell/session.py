# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: session
# -----------------------------------------------------------------------------
# Estado global de sessão do aplicativo:
#   _SESSION  — dicionário único que guarda tudo que foi computado a partir da
#               tela inicial (título, Nmin, Nmax, harmônicas, conjuntos, MPF,
#               zona de operação, limites de eixo, limiar MPF, tolerâncias).
#               É escrito UMA vez por _compute_session (compute.py) quando o
#               usuário clica em "Gerar Diagrama", e depois é lido por figure,
#               tables e por todos os callbacks_*.
#   _g(k, d)  — acessor com fallback para leitura segura (retorna `d` se `k`
#               não existir), evitando KeyError se o app for reaberto antes de
#               uma nova análise.
# Uso local monousuário — não é thread-safe nem apropriado para multi-tenant.
# =============================================================================

_SESSION = {}

def _g(key, default=None):
    """Lê um valor da sessão global com fallback."""
    return _SESSION.get(key, default)
