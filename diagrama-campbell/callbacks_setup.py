# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: callbacks_setup
# -----------------------------------------------------------------------------
# Callbacks que vivem na TELA INICIAL (entrada de dados) e a transição para
# a tela do diagrama:
#   on_tab_switch           — troca de aba de Conjunto (1..4), salvando os
#                             dados da aba atual e restaurando os da nova.
#   gerenciar_tabela        — botões + Linha / + Conjunto / Remover / Limpar
#                             (com limite de até 4 conjuntos).
#   gerar_diagrama          — botão principal "Gerar Diagrama": valida os
#                             dados via _compute_session, monta a figura
#                             inicial, popula os stores globais e alterna
#                             para a tela do diagrama.
#   nova_analise            — botão "← Nova Análise": volta à tela inicial
#                             preservando os dados já digitados.
#   render_dynamic_controls — dispara quando a sessão muda; cria dinamicamente
#                             os controles do diagrama que dependem do número
#                             de conjuntos: botões "● Conjunto N (zona)",
#                             checklist de modos por conjunto, botões do menu
#                             Excel, tabelas de cruzamento por conjunto, tabela
#                             consolidada (se N_CONJ > 1) e a tabela de pontos
#                             críticos MPF (se houver dados de MPF).
# =============================================================================

from dash import (dcc, html, callback, Input, Output, State,
                  no_update, callback_context)

from config  import NOME_BASE
from session import _g
from styles  import (get_visual, _make_zona_btn_style, _build_tabs_children,
                     _dt_wrapper_style, _dt_header_style, _EMPTY_ROW,
                     _TABS_STORE_DEFAULT)
from compute import _parse_float, _compute_session
from figure  import (gerar_figura, _apply_all_states, _recalc_mode_labels,
                     _apply_legend_key)
from tables  import (_build_table_conjunto, _build_table, _build_table_criticos)

@callback(
    Output('tabs-store',       'data',         allow_duplicate=True),
    Output('active-dt',        'data',         allow_duplicate=True),
    Output('active-dt',        'style_header', allow_duplicate=True),
    Output('active-dt-wrapper','style',        allow_duplicate=True),
    Input('conjunto-tabs', 'value'),
    State('tabs-store',  'data'),
    State('active-dt',   'data'),
    prevent_initial_call=True,
)
def on_tab_switch(new_active, tabs_store, active_data):
    store    = dict(tabs_store or _TABS_STORE_DEFAULT)
    rows     = {k: list(v) for k, v in store.get('rows', {}).items()}
    old_active = str(store.get('active', '1'))

    # Salva dados da aba que estava aberta
    rows[old_active] = active_data or []
    store['rows']    = rows
    store['active']  = str(new_active)

    c_idx    = int(new_active) - 1
    new_data = rows.get(str(new_active), [{'freq': None}] * 10)
    return store, new_data, _dt_header_style(c_idx), _dt_wrapper_style(c_idx)


# ── Gerenciar abas: + Linha / + Conjunto / Remover aba / Limpar ──────────────
@callback(
    Output('tabs-store',        'data',         allow_duplicate=True),
    Output('active-dt',         'data',         allow_duplicate=True),
    Output('active-dt',         'style_header', allow_duplicate=True),
    Output('active-dt-wrapper', 'style',        allow_duplicate=True),
    Output('conjunto-tabs',     'children',     allow_duplicate=True),
    Output('conjunto-tabs',     'value',        allow_duplicate=True),
    Input('btn-add-row', 'n_clicks'),
    Input('btn-add-col', 'n_clicks'),
    Input('btn-rem-col', 'n_clicks'),
    Input('btn-clear',   'n_clicks'),
    State('tabs-store',  'data'),
    State('active-dt',   'data'),
    prevent_initial_call=True,
)
def gerenciar_tabela(n_row, n_col, n_rem, n_clear, tabs_store, active_data):
    triggered = callback_context.triggered[0]['prop_id'].split('.')[0]

    store    = dict(tabs_store or _TABS_STORE_DEFAULT)
    rows     = {k: list(v) for k, v in store.get('rows', {}).items()}
    active   = str(store.get('active', '1'))
    n        = int(store.get('n', 1))

    # Sempre salva dados atuais antes de qualquer operação
    rows[active] = active_data or []

    if triggered == 'btn-add-row':
        rows[active] = rows[active] + [{'freq': None}]

    elif triggered == 'btn-add-col':
        if n < 4:
            n     += 1
            active = str(n)
            # Garante que a nova aba começa com dados limpos
            if str(n) not in rows or not any(
                _parse_float(r.get('freq')) for r in rows.get(str(n), [])
            ):
                rows[str(n)] = [{'freq': None}] * 10

    elif triggered == 'btn-rem-col':
        if n > 1:
            rows[str(n)] = [dict(_EMPTY_ROW)] * 10  # limpa ao remover
            n     -= 1
            active = str(n)

    elif triggered == 'btn-clear':
        rows[active] = [dict(_EMPTY_ROW)] * 10

    store['n']      = n
    store['active'] = active
    store['rows']   = rows

    c_idx        = int(active) - 1
    new_data     = rows[active]
    tabs_children = _build_tabs_children(n)

    return (store, new_data,
            _dt_header_style(c_idx), _dt_wrapper_style(c_idx),
            tabs_children, active)


# =============================================================================
# ── gerar_diagrama ────────────────────────────────────────────────────────────
# =============================================================================
@callback(
    Output('tela-inicial',       'style'),
    Output('tela-diagrama',      'style'),
    Output('session-data',       'data'),
    Output('hidden-modes',       'data',    allow_duplicate=True),
    Output('dots-on',            'data',    allow_duplicate=True),
    Output('x-min',              'value'),
    Output('x-max',              'value'),
    Output('y-min',              'value'),
    Output('y-max',              'value'),
    Output('diagrama-titulo',    'children'),
    Output('diagrama-subtitulo', 'children'),
    Output('erro-inicial',       'children'),
    Output('resonancia-graph',   'figure',  allow_duplicate=True),
    Output('ann-map',            'data',    allow_duplicate=True),
    Input('btn-gerar', 'n_clicks'),
    State('inp-titulo',     'value'),
    State('inp-nmin',       'value'),
    State('inp-nmax',       'value'),
    State('inp-harmonicas', 'value'),
    State('inp-mpf-limiar', 'value'),
    State('inp-tolerancia-min', 'value'),
    State('inp-tolerancia-max', 'value'),
    State('tabs-store',     'data'),
    State('active-dt',      'data'),
    State('lang-store',     'data'),
    prevent_initial_call=True,
)
def gerar_diagrama(n, titulo, nmin, nmax, harmonicas, mpf_limiar,
                   tolerancia_min_input, tolerancia_max_input,
                   tabs_store, active_dt_data, lang):
    show = {'display': 'block'}
    hide = {'display': 'none'}

    err = _compute_session(titulo, nmin, nmax, harmonicas, tabs_store, active_dt_data,
                           mpf_limiar, tolerancia_min_input, tolerancia_max_input)
    if err:
        return (show, hide, no_update, no_update, no_update,
                no_update, no_update, no_update, no_update,
                no_update, no_update, f"⚠ {err}",
                no_update, no_update)

    N_CONJ = _g('N_CONJ', 0)
    todos_conjuntos = _g('todos_conjuntos', [])

    hidden_modes = {str(c): [] if c == 0 else list(range(len(todos_conjuntos[c])))
                    for c in range(N_CONJ)}
    dots_on      = {"ext": True, **{str(c): (c == 0) for c in range(N_CONJ)}}

    titulo_txt    = f"{NOME_BASE} — {_g('titulo_usuario')}"
    subtitulo_txt = (f"Nmin: {_g('n_min'):.0f} rpm  ·  Nmax: {_g('n_max'):.0f} rpm  ·  "
                     f"Zona: {_g('zona_min'):.0f}–{_g('zona_max'):.0f} rpm  ·  "
                     f"{N_CONJ} conjunto(s)  ·  {len(_g('multiplicadores', []))} harmônica(s)")

    import time as _t
    session_token = {'ts': _t.time(), 'N_CONJ': N_CONJ}

    x_max_val = _g('x_max_init', 1000)
    y_max_val = _g('y_max_init', 100)

    fig, ann_map = gerar_figura(0, x_max_val, 0, y_max_val, lang=lang or 'pt')
    _apply_all_states(fig, ann_map, hidden_modes, True, dots_on)

    visible_sets = {}
    for c in range(N_CONJ):
        all_i = set(range(len(todos_conjuntos[c])))
        hid_i = set(hidden_modes.get(str(c), []))
        visible_sets[c] = all_i - hid_i
    _recalc_mode_labels(fig, ann_map, visible_sets, x_max_val, 0, y_max_val)
    _apply_legend_key(fig, dots_on, hidden_modes)

    return (hide, show, session_token, hidden_modes, dots_on,
            0, x_max_val, 0, y_max_val,
            titulo_txt, subtitulo_txt, '',
            fig, ann_map)


# ── Nova Análise (volta para tela inicial) ────────────────────────────────────
@callback(
    Output('tela-inicial',  'style', allow_duplicate=True),
    Output('tela-diagrama', 'style', allow_duplicate=True),
    Input('btn-nova-analise', 'n_clicks'),
    prevent_initial_call=True,
)
def nova_analise(n):
    return {'display': 'block'}, {'display': 'none'}


# ── Preenche os controles dinâmicos quando a sessão muda ──────────────────────
@callback(
    Output('zona-buttons-container',  'children'),
    Output('modos-panel-content',     'children'),
    Output('excel-buttons-container', 'children'),
    Output('tabelas-cruzamento',      'children'),
    Input('session-data', 'data'),
    prevent_initial_call=True,
)
def render_dynamic_controls(session_token):
    N_CONJ          = _g('N_CONJ', 0)
    todos_conjuntos = _g('todos_conjuntos', [])
    if N_CONJ == 0:
        return [], [], [], []

    zona_btns = [
        html.Button(
            f"● {get_visual(c)['nome']} (zona)",
            id={'type': 'zona-toggle', 'index': c},
            n_clicks=0,
            style=_make_zona_btn_style(c, c == 0),
        )
        for c in range(N_CONJ)
    ]

    checklist_secs = []
    for c in range(N_CONJ):
        vis_c = get_visual(c)
        checklist_secs.append(html.Div([
            html.Div(f"▸ {vis_c['nome']}", style={
                'padding': '6px 10px 2px', 'fontWeight': 'bold', 'fontSize': '11px',
                'color': vis_c['cor_linha'] if vis_c['cor_linha'] != 'black' else '#333',
                'borderTop': '1px solid #eee' if c > 0 else 'none',
            }),
            dcc.Checklist(
                id={'type': 'modos-checklist', 'index': c},
                options=[{'label': f'  M{i+1:02d}  ({f} Hz)', 'value': i}
                         for i, f in enumerate(todos_conjuntos[c])],
                value=list(range(len(todos_conjuntos[c]))) if c == 0 else [],
                labelStyle={'display': 'block', 'padding': '4px 10px',
                            'fontSize': '12px', 'cursor': 'pointer', 'whiteSpace': 'nowrap'},
                inputStyle={'marginRight': '6px'},
            ),
        ]))

    excel_btns = [
        html.Button(
            f"  {get_visual(c)['nome']}",
            id={'type': 'excel-export-btn', 'index': c},
            n_clicks=0,
            style={'background': get_visual(c)['btn_color'], 'color': 'white',
                   'border': 'none', 'borderRadius': '5px', 'padding': '5px 10px',
                   'fontSize': '12px', 'fontWeight': 'bold', 'cursor': 'pointer',
                   'width': '100%', 'textAlign': 'left', 'marginBottom': '2px'},
        )
        for c in range(N_CONJ)
    ]

    table_children = []
    for c in range(N_CONJ):
        vis_c = get_visual(c)
        table_children.append(html.Div([
            html.Div(vis_c['nome'], style={
                'fontWeight': 'bold', 'fontSize': '13px', 'color': vis_c['btn_color'],
                'padding': '6px 0 4px',
                'borderLeft': f"4px solid {vis_c['btn_color']}",
                'paddingLeft': '8px', 'marginBottom': '4px',
            }),
            html.Div(_build_table_conjunto(c), style={
                'overflowX': 'auto', 'overflowY': 'auto', 'maxHeight': '240px',
                'border': f"1px solid {vis_c['btn_color']}", 'borderRadius': '6px',
            }),
        ], style={'marginBottom': '12px'}))

    if N_CONJ > 1:
        table_children.append(html.Div([
            html.Div("Todos os Conjuntos", style={
                'fontWeight': 'bold', 'fontSize': '13px', 'color': '#333',
                'padding': '6px 0 4px', 'borderLeft': '4px solid #555',
                'paddingLeft': '8px', 'marginBottom': '4px',
            }),
            html.Div(_build_table(), style={
                'overflowX': 'auto', 'overflowY': 'auto', 'maxHeight': '280px',
                'border': '1px solid #999', 'borderRadius': '6px',
            }),
        ]))

    # ── Pontos Críticos MPF (exibido apenas se dados de MPF existirem) ────────
    tabela_crit = _build_table_criticos()
    if tabela_crit is not None:
        table_children.append(html.Div([
            html.Div(f"📊 Massa Efetiva Modal por Modo  (vermelho = participação > {_g('mpf_limiar', 5.0):.4g}%)", style={
                'fontWeight': 'bold', 'fontSize': '13px', 'color': '#856404',
                'padding': '6px 0 4px',
                'borderLeft': '4px solid #f0c040',
                'paddingLeft': '8px', 'marginBottom': '4px',
                'background': '#fffbea', 'borderRadius': '0 4px 4px 0',
            }),
            html.Div(tabela_crit, style={
                'overflowX': 'auto', 'overflowY': 'auto', 'maxHeight': '320px',
                'border': '1px solid #f0c040', 'borderRadius': '6px',
            }),
        ], style={'marginTop': '16px'}))

    return zona_btns, checklist_secs, excel_btns, table_children


