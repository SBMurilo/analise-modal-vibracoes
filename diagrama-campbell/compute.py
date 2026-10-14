# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: compute
# -----------------------------------------------------------------------------
# Validação e pré-processamento dos dados da TELA INICIAL:
#   _parse_float(s)         — parser tolerante que aceita "1,5" ou "1.5" e
#                             retorna None para valores inválidos ou vazios
#                             (usado por _compute_session e por todos os
#                             callbacks que leem valores do DataTable).
#   _compute_session(...)   — recebe título, Nmin, Nmax, harmônicas, dados
#                             das abas (tabs_store + DataTable ativo), limiar
#                             MPF e as duas tolerâncias (min/max) da zona.
#                             Valida tudo, ordena os conjuntos de frequências,
#                             calcula a zona de operação, o RPM máximo do
#                             eixo X e o Y máximo, e escreve _SESSION com
#                             todos os campos consumidos pelo restante do
#                             app. Retorna '' em caso de sucesso, ou uma
#                             mensagem de erro concatenada (mostrada no
#                             rodapé da tela inicial em vermelho).
# =============================================================================

import numpy as np
import re as _re

from session import _SESSION
from styles import _TABS_STORE_DEFAULT

def _parse_float(s):
    if s is None:
        return None
    try:
        return float(str(s).strip().replace(',', '.'))
    except (ValueError, TypeError):
        return None


def _compute_session(titulo, nmin, nmax, harmonicas_str, tabs_store, active_dt_data,
                     mpf_limiar=5.0, tolerancia_min_input=10.0, tolerancia_max_input=10.0):
    """
    Valida os dados da tela inicial e preenche _SESSION globalmente.
    Retorna '' se OK, ou mensagem de erro.
    tabs_store : dict do store 'tabs-store'
    active_dt_data : list[dict] com dados atuais do DataTable ativo
    mpf_limiar : float — limiar de participação modal efetiva (%)
    tolerancia_min_input : float — tolerância à esquerda de Nmin em % (ex: 10 = -10%)
    tolerancia_max_input : float — tolerância à direita de Nmax em % (ex: 15 = +15%)
    """
    erros = []

    titulo = (titulo or '').strip() or 'Sem Título'
    titulo_arquivo = _re.sub(r'[\\/*?:"<>|]', '', titulo).strip().replace(' ', '_')

    n_min = _parse_float(nmin)
    n_max = _parse_float(nmax)
    if n_min is None or n_max is None:
        erros.append("Nmin e Nmax devem ser números.")
    elif n_min > n_max:
        erros.append("Nmin não pode ser maior que Nmax.")

    mults = []
    for tok in str(harmonicas_str or '').replace(';', ',').split(','):
        v = _parse_float(tok.strip())
        if v is not None and v > 0:
            mults.append(v)
    if not mults:
        erros.append("Informe pelo menos uma Harmônica (ex: 1, 3, 5).")

    # ── lê dados de cada aba ─────────────────────────────────────────────────
    store     = tabs_store or _TABS_STORE_DEFAULT
    n_tabs    = int(store.get('n', 1))
    active_k  = str(store.get('active', '1'))
    rows_all  = {k: list(v) for k, v in store.get('rows', {}).items()}
    # dados do DataTable ativo podem estar mais recentes que o store
    if active_dt_data is not None:
        rows_all[active_k] = active_dt_data

    conjuntos = []
    mpf_data  = []   # paralelo a conjuntos: list[list[{'x','y','z'}]]
    for i in range(1, n_tabs + 1):
        key  = str(i)
        rows = rows_all.get(key, [])
        pairs = []   # (freq, x_pct, y_pct, z_pct)
        for row in rows:
            v = _parse_float(row.get('freq'))
            if v is not None and v > 0:
                pairs.append((
                    v,
                    _parse_float(row.get('x_pct')),
                    _parse_float(row.get('y_pct')),
                    _parse_float(row.get('z_pct')),
                ))
        if pairs:
            pairs.sort(key=lambda t: t[0])
            conjuntos.append([p[0] for p in pairs])
            mpf_data.append([{'x': p[1], 'y': p[2], 'z': p[3]} for p in pairs])

    if not conjuntos:
        erros.append("Preencha ao menos um conjunto de Frequências Naturais.")

    if erros:
        return ' · '.join(erros)

    mults = sorted(set(mults))
    # Tolerâncias dinâmicas e independentes para Nmin e Nmax (% → decimal)
    def _to_dec(v, default=0.10):
        try:
            d = float(v) / 100.0
        except (TypeError, ValueError):
            return default
        return d if d > 0 else default

    tolerancia_min = _to_dec(tolerancia_min_input)
    tolerancia_max = _to_dec(tolerancia_max_input)

    if n_min == n_max:
        # Ponto de operação único: zona é -tol_min a +tol_max em torno da velocidade
        zona_min = n_min * (1 - tolerancia_min)
        zona_max = n_max * (1 + tolerancia_max)
    else:
        zona_min = n_min * (1 - tolerancia_min)
        zona_max = n_max * (1 + tolerancia_max)
    rpm_max_raw = zona_max * 1.5
    rpm_max     = int(np.ceil(rpm_max_raw / 50) * 50)
    _y_max_all  = max(max(c) for c in conjuntos)
    y_max_init  = int(np.ceil(_y_max_all * 1.3 / 10) * 10)
    x_max_init  = rpm_max
    N_CONJ      = len(conjuntos)

    _SESSION.clear()
    _SESSION.update(
        titulo_usuario  = titulo,
        titulo_arquivo  = titulo_arquivo,
        n_min           = n_min,
        n_max           = n_max,
        multiplicadores = mults,
        todos_conjuntos = conjuntos,
        todos_mpf       = mpf_data,
        N_CONJ          = N_CONJ,
        zona_min        = zona_min,
        zona_max        = zona_max,
        rpm_max         = rpm_max,
        _y_max_all      = _y_max_all,
        y_max_init      = y_max_init,
        x_max_init      = x_max_init,
        mpf_limiar      = mpf_limiar if mpf_limiar is not None and mpf_limiar > 0 else 5.0,
        tolerancia_min  = tolerancia_min,
        tolerancia_max  = tolerancia_max,
    )
    return ''

