# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: callbacks_diagram
# -----------------------------------------------------------------------------
# Callbacks que vivem na TELA DO DIAGRAMA (interações no gráfico e nos botões
# do cabeçalho). Todos operam sobre a figura Plotly e os stores globais
# (hidden-modes, dots-on, labels-on, ann-map, lang-store):
#   atualizar                — X min/max, Y min/max (reconstroi a figura via
#                              gerar_figura + _apply_all_states).
#   toggle_labels            — botão "Labels ON/OFF" (mostra/oculta plaquinhas
#                              RPM dos cruzamentos).
#   toggle_any_dropdown      — abre/fecha ▼ Pontos / ▼ Modos / ▼ Excel de
#                              forma mutuamente exclusiva.
#   toggle_ext_dots          — botão "Externos" (pontos verdes fora da zona).
#   toggle_zona_dots         — botões "● Conjunto N (zona)" — liga/desliga os
#                              pontos de cruzamento dentro da zona por conjunto.
#   toggle_modos_checklist   — checklist de modos ativos por conjunto (M01,
#                              M02, ...); atualiza hidden-modes + figura.
#   sync_legend_modos        — sincroniza o checklist quando o usuário clica
#                              diretamente no legendgroup do modo no gráfico.
#   aplicar_criticos         — botão "⚠ Críticos": filtra para exibir só modos
#                              com MPF > limiar E cruzamento na zona; também
#                              ATIVA automaticamente "◆ Pontos MPF" (Rev05.1).
#   toggle_mpf_vivid         — botão "◆ Pontos MPF" (borda azul + tamanho
#                              maior nos cruzamentos críticos).
#   selecionar_idioma        — botões PT / EN / ES (reconstroi a figura com
#                              textos traduzidos preservando o estado atual).
#   [clientside] labels-on → plaquinhas RPM ; restyleData → sincroniza as
#                              plaquinhas com a visibilidade das harmônicas
#                              alternada pelo usuário na legenda do Plotly.
# -----------------------------------------------------------------------------
# Rev05.1 (2026-08-14):
#   • Botão "⚠ Críticos" agora aciona automaticamente "◆ Pontos MPF" (borda
#     azul + tamanho maior nos cruzamentos críticos) e atualiza o estilo do
#     botão para o estado ativo. O usuário pode desmarcar manualmente no
#     dropdown "▼ Pontos" para remover a borda. Vale para qualquer número de
#     conjuntos, pois a lógica de destaque MPF depende apenas do estado
#     dots_on["mpf_vivid"] (que passa a True) e de _is_mpf_critico_na_zona.
#   Nenhuma outra callback foi tocada.
# =============================================================================

import json
import numpy as np
import plotly.graph_objects as go

from dash import (callback, clientside_callback, Input, Output, State,
                  no_update, ALL, callback_context)

from config  import FIG_HEIGHT
from session import _SESSION, _g
from styles  import (get_visual, _make_ext_btn_style, _make_zona_btn_style,
                     _make_mpf_btn_style, BTN_ON_STYLE, BTN_OFF_STYLE)
from figure  import (gerar_figura, _apply_all_states, _recalc_mode_labels,
                     _is_mpf_critico_na_zona, _apply_legend_key)

@callback(
    Output('resonancia-graph', 'figure'),
    Output('ann-map', 'data'),
    Input('x-min', 'value'),
    Input('x-max', 'value'),
    Input('y-min', 'value'),
    Input('y-max', 'value'),
    State('hidden-modes', 'data'),
    State('labels-on',    'data'),
    State('dots-on',      'data'),
    State('lang-store',   'data'),
)
def atualizar(x_min, x_max, y_min, y_max, hidden_modes, labels_on, dots_on, lang):
    if not _SESSION:
        return no_update, no_update

    N_CONJ          = _g('N_CONJ', 0)
    todos_conjuntos = _g('todos_conjuntos', [])
    rpm_max         = _g('rpm_max', 1000)
    _y_max_all      = _g('_y_max_all', 100)
    y_max_init      = _g('y_max_init', 100)

    x_min     = x_min  if x_min  is not None else 0
    x_max     = x_max  if x_max  is not None else rpm_max
    y_min     = y_min  if y_min  is not None else 0
    y_max_raw = y_max  if y_max  is not None else _y_max_all * 1.3
    y_max     = int(np.ceil(y_max_raw / 10) * 10)

    _init_hidden_modes = {str(c): [] if c == 0 else list(range(len(todos_conjuntos[c])))
                          for c in range(N_CONJ)}
    _init_dots_on      = {"ext": True, **{str(c): (c == 0) for c in range(N_CONJ)}}

    hidden_modes = hidden_modes or _init_hidden_modes
    labels_on    = labels_on   if labels_on is not None else True
    dots_on      = dots_on     or _init_dots_on

    fig, ann_map = gerar_figura(x_min, x_max, y_min, y_max,
                                fig_height=FIG_HEIGHT, lang=lang or 'pt')
    _apply_all_states(fig, ann_map, hidden_modes, labels_on, dots_on)

    visible_sets_init = {}
    for c_i in range(N_CONJ):
        all_idx  = set(range(len(todos_conjuntos[c_i])))
        hidden_i = set(hidden_modes.get(str(c_i), []))
        visible_sets_init[c_i] = all_idx - hidden_i
    _recalc_mode_labels(fig, ann_map, visible_sets_init,
                        x_max, y_min, y_max, fig_height=FIG_HEIGHT, x_min=x_min)
    _apply_legend_key(fig, dots_on, hidden_modes)

    return fig, ann_map


@callback(
    Output('labels-on',     'data'),
    Output('labels-toggle', 'children'),
    Output('labels-toggle', 'style'),
    Input('labels-toggle',  'n_clicks'),
    prevent_initial_call=True,
)
def toggle_labels(n_clicks):
    on    = (n_clicks % 2 == 0)
    text  = "Labels ON" if on else "Labels OFF"
    style = ({**BTN_ON_STYLE,  'height': '32px', 'padding': '0 14px', 'marginRight': '8px'} if on
             else {**BTN_OFF_STYLE, 'height': '32px', 'padding': '0 14px', 'marginRight': '8px'})
    return on, text, style


@callback(
    Output('pontos-dropdown-panel', 'style', allow_duplicate=True),
    Output('modos-dropdown-panel',  'style', allow_duplicate=True),
    Output('excel-dropdown-panel',  'style', allow_duplicate=True),
    Input('pontos-dropdown-btn', 'n_clicks'),
    Input('modos-dropdown-btn',  'n_clicks'),
    Input('excel-dropdown-btn',  'n_clicks'),
    Input('close-all-dropdowns', 'n_clicks'),
    State('pontos-dropdown-panel', 'style'),
    State('modos-dropdown-panel',  'style'),
    State('excel-dropdown-panel',  'style'),
    prevent_initial_call=True,
)
def toggle_any_dropdown(n_pontos, n_modos, n_excel, n_outside,
                        st_pontos, st_modos, st_excel):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    def _closed(st):
        s = dict(st); s['display'] = 'none'; return s

    def _toggle(st):
        s = dict(st)
        s['display'] = 'none' if s.get('display') != 'none' else 'block'
        return s

    if trigger_id == 'close-all-dropdowns':
        return _closed(st_pontos), _closed(st_modos), _closed(st_excel)
    elif trigger_id == 'pontos-dropdown-btn':
        return _toggle(st_pontos), _closed(st_modos), _closed(st_excel)
    elif trigger_id == 'modos-dropdown-btn':
        return _closed(st_pontos), _toggle(st_modos), _closed(st_excel)
    elif trigger_id == 'excel-dropdown-btn':
        return _closed(st_pontos), _closed(st_modos), _toggle(st_excel)
    return no_update, no_update, no_update


@callback(
    Output('dots-on',          'data'),
    Output('green-ext-toggle', 'style'),
    Output('resonancia-graph', 'figure', allow_duplicate=True),
    Input('green-ext-toggle',  'n_clicks'),
    State('dots-on',           'data'),
    State('resonancia-graph',  'figure'),
    State('hidden-modes',      'data'),
    prevent_initial_call=True,
)
def toggle_ext_dots(n_clicks, dots_on, current_figure, hidden_modes):
    N_CONJ  = _g('N_CONJ', 0)
    _init   = {"ext": True, **{str(c): (c == 0) for c in range(N_CONJ)}}
    dots_on = dict(dots_on or _init)
    on      = not dots_on.get("ext", True)
    dots_on["ext"] = on
    if current_figure is None:
        return dots_on, _make_ext_btn_style(on), no_update
    fig = go.Figure(current_figure)
    for t in fig.data:
        if not hasattr(t, 'customdata') or t.customdata is None or len(t.customdata) == 0: continue
        cd = t.customdata[0]
        if not isinstance(cd, str) or not cd.startswith('ext_') or '_conj_' not in cd: continue
        try:
            c_t = int(cd.rsplit('_conj_', 1)[1].split('_modo_')[0])
        except (ValueError, IndexError): continue
        zona_on   = bool(dots_on.get(str(c_t), c_t == 0))
        t.visible = on and zona_on
    _apply_legend_key(fig, dots_on, hidden_modes)
    return dots_on, _make_ext_btn_style(on), fig


@callback(
    Output('dots-on',                             'data',   allow_duplicate=True),
    Output({'type': 'zona-toggle', 'index': ALL}, 'style'),
    Output('resonancia-graph',                    'figure', allow_duplicate=True),
    Input({'type': 'zona-toggle', 'index': ALL},  'n_clicks'),
    State('dots-on',          'data'),
    State('resonancia-graph', 'figure'),
    State('ann-map',          'data'),
    State('labels-on',        'data'),
    State('hidden-modes',     'data'),
    prevent_initial_call=True,
)
def toggle_zona_dots(n_clicks_list, dots_on, current_figure,
                     ann_map, labels_on, hidden_modes):
    N_CONJ          = _g('N_CONJ', 0)
    multiplicadores = _g('multiplicadores', [])
    _init           = {"ext": True, **{str(c): (c == 0) for c in range(N_CONJ)}}
    ctx = callback_context
    if not ctx.triggered:
        return no_update, [no_update] * N_CONJ, no_update
    try:
        prop_id = ctx.triggered[0]['prop_id']
        btn_id  = json.loads(prop_id.rsplit('.', 1)[0])
        c       = int(btn_id['index'])
    except Exception:
        return no_update, [no_update] * N_CONJ, no_update
    if not n_clicks_list[c]:
        return no_update, [no_update] * N_CONJ, no_update
    dots_on      = dict(dots_on or _init)
    new_val      = not dots_on.get(str(c), c == 0)
    dots_on[str(c)] = new_val
    styles = [_make_zona_btn_style(c2, bool(dots_on.get(str(c2), c2 == 0)))
              for c2 in range(N_CONJ)]
    if current_figure is None:
        return dots_on, styles, no_update
    fig   = go.Figure(current_figure)
    ext_on = bool(dots_on.get("ext", True))
    vis_c  = get_visual(c)
    _CORES_ZONA_C = {vis_c['cor_ponto_zona'], vis_c['cor_ponto_zona_t']}
    for t in fig.data:
        if not hasattr(t, 'customdata') or t.customdata is None or len(t.customdata) == 0:
            if hasattr(t, 'marker') and getattr(t.marker, 'color', None) in _CORES_ZONA_C:
                t.visible = new_val
            continue
        cd = t.customdata[0]
        if not isinstance(cd, str): continue
        if cd.startswith('cruzamento_') and f'_conj_{c}_' in cd:
            t.visible = new_val
        elif cd.startswith('ext_') and f'_conj_{c}_' in cd:
            t.visible = new_val and ext_on
    if ann_map:
        labels_on_bool = bool(labels_on) if labels_on is not None else True
        hidden_c       = set(hidden_modes.get(str(c), []) if hidden_modes else [])
        annotations    = list(fig.layout.annotations)
        for m in multiplicadores:
            key = f"harm_{m}"
            if key not in ann_map: continue
            for entry in (ann_map[key] or []):
                if isinstance(entry, (list, tuple)) and len(entry) >= 3:
                    ann_idx, c_e, i_e = int(entry[0]), int(entry[1]), int(entry[2])
                    if c_e != c or ann_idx >= len(annotations): continue
                    annotations[ann_idx].visible = new_val and labels_on_bool and (i_e not in hidden_c)
        fig.layout.annotations = annotations
    _apply_legend_key(fig, dots_on, hidden_modes)
    return dots_on, styles, fig


@callback(
    Output('hidden-modes',     'data'),
    Output('resonancia-graph', 'figure', allow_duplicate=True),
    Input({'type': 'modos-checklist', 'index': ALL}, 'value'),
    State('resonancia-graph', 'figure'),
    State('ann-map',          'data'),
    State('labels-on',        'data'),
    State('dots-on',          'data'),
    prevent_initial_call=True,
)
def toggle_modos_checklist(visible_values_per_set, current_figure,
                            ann_map, labels_on, dots_on):
    if current_figure is None:
        return no_update, no_update
    N_CONJ          = _g('N_CONJ', 0)
    todos_conjuntos = _g('todos_conjuntos', [])
    rpm_max         = _g('rpm_max', 1000)
    y_max_init      = _g('y_max_init', 100)

    hidden_modes = {}
    for c, vis_vals in enumerate(visible_values_per_set):
        all_idx      = set(range(len(todos_conjuntos[c])))
        visible_set  = set(vis_vals or [])
        hidden_modes[str(c)] = list(all_idx - visible_set)

    fig = go.Figure(current_figure)
    _apply_all_states(fig, ann_map or {}, hidden_modes, labels_on, dots_on)

    try:
        xr      = fig.layout.xaxis.range or [0, rpm_max]
        yr      = fig.layout.yaxis.range or [0, y_max_init]
        x_min_r, x_max_r = float(xr[0]), float(xr[1])
        y_min_r, y_max_r = float(yr[0]), float(yr[1])
    except Exception:
        x_min_r, x_max_r = 0, rpm_max
        y_min_r, y_max_r = 0, y_max_init

    visible_sets_new = {}
    for c in range(N_CONJ):
        all_idx = set(range(len(todos_conjuntos[c])))
        hidden  = set(hidden_modes.get(str(c), []))
        visible_sets_new[c] = all_idx - hidden

    _recalc_mode_labels(fig, ann_map or {}, visible_sets_new,
                        x_max_r, y_min_r, y_max_r,
                        fig_height=FIG_HEIGHT, x_min=x_min_r)
    _apply_legend_key(fig, dots_on, hidden_modes)
    return hidden_modes, fig


@callback(
    Output('hidden-modes',                            'data',  allow_duplicate=True),
    Output({'type': 'modos-checklist', 'index': ALL}, 'value'),
    Input('resonancia-graph', 'restyleData'),
    State('resonancia-graph', 'figure'),
    State('hidden-modes',     'data'),
    prevent_initial_call=True,
)
def sync_legend_modos(restyle_data, current_figure, hidden_modes):
    N_CONJ          = _g('N_CONJ', 0)
    todos_conjuntos = _g('todos_conjuntos', [])
    if not restyle_data or not current_figure:
        return no_update, [no_update] * N_CONJ
    changes       = restyle_data[0]
    trace_indices = restyle_data[1]
    if 'visible' not in changes:
        return no_update, [no_update] * N_CONJ
    traces        = current_figure.get('data', [])
    affected_conj = set()
    for ti in trace_indices:
        if ti < len(traces):
            lg = traces[ti].get('legendgroup', '')
            if lg.startswith('modos_'):
                try: affected_conj.add(int(lg.split('_')[1]))
                except (ValueError, IndexError): pass
    if not affected_conj:
        return no_update, [no_update] * N_CONJ
    new_vis    = changes['visible']
    if isinstance(new_vis, list): new_vis = new_vis[0]
    is_visible = new_vis not in (False, 'legendonly')
    hidden_modes   = dict(hidden_modes or {})
    checklist_vals = [no_update] * N_CONJ
    for c in affected_conj:
        all_idx = list(range(len(todos_conjuntos[c])))
        if is_visible:
            hidden_modes[str(c)] = [];      checklist_vals[c] = all_idx
        else:
            hidden_modes[str(c)] = all_idx; checklist_vals[c] = []
    return hidden_modes, checklist_vals


# ── Botão Críticos: atalho que mostra só modos com MPF > limiar na zona ──────
# Rev05.1: além de filtrar os modos críticos, este callback agora ATIVA o
# destaque "◆ Pontos MPF" (borda azul + tamanho maior nos cruzamentos críticos)
# e atualiza o estilo do próprio botão MPF. O usuário pode desmarcar
# manualmente no dropdown "▼ Pontos" (que dispara toggle_mpf_vivid).
@callback(
    Output('hidden-modes',                            'data',  allow_duplicate=True),
    Output({'type': 'modos-checklist', 'index': ALL}, 'value', allow_duplicate=True),
    Output('resonancia-graph', 'figure', allow_duplicate=True),
    Output('dots-on',          'data',   allow_duplicate=True),   # Rev05.1
    Output('mpf-vivid-toggle', 'style',  allow_duplicate=True),   # Rev05.1
    Input('btn-criticos', 'n_clicks'),
    State('resonancia-graph', 'figure'),
    State('ann-map',          'data'),
    State('labels-on',        'data'),
    State('dots-on',          'data'),
    prevent_initial_call=True,
)
def aplicar_criticos(n_clicks, current_figure, ann_map, labels_on, dots_on):
    N_CONJ          = _g('N_CONJ', 0)
    todos_conjuntos = _g('todos_conjuntos', [])
    todos_mpf       = _g('todos_mpf', [])
    multiplicadores = _g('multiplicadores', [])
    zona_min        = _g('zona_min', 0)
    zona_max        = _g('zona_max', 0)
    rpm_max         = _g('rpm_max', 1000)
    y_max_init      = _g('y_max_init', 100)
    MPF_LIMIAR      = _g('mpf_limiar', 5.0)

    if not todos_conjuntos or current_figure is None:
        # Preserva os 5 outputs mesmo em early-return.
        return (no_update, [no_update] * max(N_CONJ, 1), no_update,
                no_update, no_update)

    # Quais modos de cada conjunto têm MPF > limiar E cruzam a zona
    criticos_por_conj = {}
    for c, conj in enumerate(todos_conjuntos):
        mpf_c   = todos_mpf[c] if todos_mpf and c < len(todos_mpf) else []
        criticos = set()
        for i_f, f in enumerate(conj):
            mpf  = mpf_c[i_f] if i_f < len(mpf_c) else {}
            vals = [v for v in (mpf.get('x'), mpf.get('y'), mpf.get('z')) if v is not None]
            if not vals or not any(v > MPF_LIMIAR for v in vals):
                continue
            for m in multiplicadores:
                if zona_min <= (f * 60) / m <= zona_max:
                    criticos.add(i_f)
                    break
        criticos_por_conj[c] = criticos

    hidden_modes     = {}
    checklist_values = []
    _dots = dots_on or {"ext": True, **{str(c): (c == 0) for c in range(N_CONJ)}}
    for c in range(N_CONJ):
        all_idx  = set(range(len(todos_conjuntos[c])))
        conjunto_ativo = bool(_dots.get(str(c), c == 0))

        if not conjunto_ativo:
            # conjunto com pontos desativados → esconde todos os modos
            hidden_modes[str(c)] = list(all_idx)
            checklist_values.append([])
            continue

        criticos = criticos_por_conj.get(c, set())
        if not criticos:          # ativo mas sem críticos: mantém todos
            hidden_modes[str(c)] = []
            checklist_values.append(list(all_idx))
        else:
            hidden_modes[str(c)] = list(all_idx - criticos)
            checklist_values.append(list(criticos))

    fig = go.Figure(current_figure)
    _apply_all_states(fig, ann_map or {}, hidden_modes, labels_on, dots_on)

    try:
        xr = fig.layout.xaxis.range or [0, rpm_max]
        yr = fig.layout.yaxis.range or [0, y_max_init]
        x_min_r, x_max_r = float(xr[0]), float(xr[1])
        y_min_r, y_max_r = float(yr[0]), float(yr[1])
    except Exception:
        x_min_r, x_max_r = 0, rpm_max
        y_min_r, y_max_r = 0, y_max_init

    visible_sets = {c: set(range(len(todos_conjuntos[c]))) - set(hidden_modes.get(str(c), []))
                    for c in range(N_CONJ)}
    _recalc_mode_labels(fig, ann_map or {}, visible_sets,
                        x_max_r, y_min_r, y_max_r,
                        fig_height=FIG_HEIGHT, x_min=x_min_r)

    # ── Rev05.1: ativa "◆ Pontos MPF" automaticamente ─────────────────────────
    # Muda o estado global e aplica o mesmo estilo vívido usado em
    # toggle_mpf_vivid (borda azul + tamanho 16) aos pontos que atendem
    # _is_mpf_critico_na_zona. Isso é feito DEPOIS de _apply_all_states para
    # que o estilo vívido sobrescreva o estilo neutro dos pontos ativos.
    dots_on_new = dict(_dots)
    dots_on_new["mpf_vivid"] = True
    for t in fig.data:
        if not hasattr(t, 'customdata') or not t.customdata or not t.customdata[0]:
            continue
        cd = t.customdata[0]
        if not isinstance(cd, str) or not cd.startswith('cruzamento_') or '_conj_' not in cd:
            continue
        try:
            tail = cd.rsplit('_conj_', 1)[1]
            c_t  = int(tail.split('_modo_')[0])
            i_t  = int(tail.split('_modo_')[1])
        except (ValueError, IndexError):
            continue
        if not _is_mpf_critico_na_zona(c_t, i_t):
            continue
        # Aplica os mesmos valores usados em toggle_mpf_vivid quando on=True.
        t.marker.size       = 16
        t.marker.line.color = '#1565c0'
        t.marker.line.width = 2.5

    # Recalcula a legenda-chave com o novo dots_on (para que a entrada
    # "Cruzamentos Críticos - MPF > X%" apareça se houver algum crítico visível).
    _apply_legend_key(fig, dots_on_new, hidden_modes)

    return (hidden_modes, checklist_values, fig,
            dots_on_new, _make_mpf_btn_style(True))


# ── Botão Pontos MPF: destaca pontos com dados MPF (maior + borda azul) ───────
@callback(
    Output('dots-on',          'data',   allow_duplicate=True),
    Output('mpf-vivid-toggle', 'style'),
    Output('resonancia-graph', 'figure', allow_duplicate=True),
    Input('mpf-vivid-toggle',  'n_clicks'),
    State('dots-on',           'data'),
    State('resonancia-graph',  'figure'),
    State('hidden-modes',      'data'),
    prevent_initial_call=True,
)
def toggle_mpf_vivid(n_clicks, dots_on, current_figure, hidden_modes):
    N_CONJ    = _g('N_CONJ', 0)
    _init     = {"ext": True, **{str(c): (c == 0) for c in range(N_CONJ)}}
    dots_on   = dict(dots_on or _init)
    on        = not dots_on.get("mpf_vivid", False)
    dots_on["mpf_vivid"] = on

    if current_figure is None:
        return dots_on, _make_mpf_btn_style(on), no_update

    fig = go.Figure(current_figure)
    for t in fig.data:
        if not hasattr(t, 'customdata') or not t.customdata or not t.customdata[0]:
            continue
        cd = t.customdata[0]
        if not isinstance(cd, str) or not cd.startswith('cruzamento_') or '_conj_' not in cd:
            continue
        try:
            tail = cd.rsplit('_conj_', 1)[1]
            c_t  = int(tail.split('_modo_')[0])
            i_t  = int(tail.split('_modo_')[1])
        except (ValueError, IndexError):
            continue
        if not _is_mpf_critico_na_zona(c_t, i_t):
            continue
        vis_c = get_visual(c_t)
        if on:
            t.marker.size       = 16
            t.marker.line.color = '#1565c0'
            t.marker.line.width = 2.5
        else:
            t.marker.size       = 11
            t.marker.line.color = vis_c['cor_ponto_zona_linha']
            t.marker.line.width = 2.0

    _apply_legend_key(fig, dots_on, hidden_modes)
    return dots_on, _make_mpf_btn_style(on), fig


# ── Seletor de idioma ─────────────────────────────────────────────────────────
@callback(
    Output('lang-store',                              'data'),
    Output({'type': 'lang-btn', 'index': ALL},        'style'),
    Output('resonancia-graph', 'figure', allow_duplicate=True),
    Output('ann-map',          'data',   allow_duplicate=True),
    Input({'type': 'lang-btn', 'index': ALL}, 'n_clicks'),
    State('lang-store',        'data'),
    State('resonancia-graph',  'figure'),
    State('hidden-modes',      'data'),
    State('labels-on',         'data'),
    State('dots-on',           'data'),
    prevent_initial_call=True,
)
def selecionar_idioma(n_clicks_list, current_lang, current_figure,
                      hidden_modes, labels_on, dots_on):
    LANG_CODES = ['pt', 'en', 'es']
    ctx = callback_context
    if not ctx.triggered:
        return no_update, [no_update] * 3, no_update, no_update
    try:
        btn_id   = json.loads(ctx.triggered[0]['prop_id'].rsplit('.', 1)[0])
        new_lang = btn_id['index']
    except Exception:
        return no_update, [no_update] * 3, no_update, no_update

    # Estilos dos botões: ativo = azul, inativo = cinza
    styles = [
        dict(background='#2980b9' if c == new_lang else '#bdc3c7',
             color='white', border='none', borderRadius='5px',
             padding='4px 10px', fontSize='12px', fontWeight='bold',
             cursor='pointer', marginLeft='3px')
        for c in LANG_CODES
    ]

    if not _SESSION or current_figure is None:
        return new_lang, styles, no_update, no_update

    # Regera o gráfico com novo idioma mantendo range atual
    N_CONJ          = _g('N_CONJ', 0)
    todos_conjuntos = _g('todos_conjuntos', [])
    rpm_max         = _g('rpm_max', 1000)
    y_max_init      = _g('y_max_init', 100)

    try:
        fig_cur  = go.Figure(current_figure)
        xr       = fig_cur.layout.xaxis.range or [0, rpm_max]
        yr       = fig_cur.layout.yaxis.range or [0, y_max_init]
        x_min_r, x_max_r = float(xr[0]), float(xr[1])
        y_min_r, y_max_r = float(yr[0]), float(yr[1])
    except Exception:
        x_min_r, x_max_r = 0, rpm_max
        y_min_r, y_max_r = 0, y_max_init

    fig, ann_map = gerar_figura(x_min_r, x_max_r, y_min_r, y_max_r,
                                fig_height=FIG_HEIGHT, lang=new_lang)
    _init_hm = {str(c): [] if c == 0 else list(range(len(todos_conjuntos[c])))
                for c in range(N_CONJ)}
    _init_do = {"ext": True, **{str(c): (c == 0) for c in range(N_CONJ)}}
    _apply_all_states(fig, ann_map,
                      hidden_modes or _init_hm,
                      labels_on if labels_on is not None else True,
                      dots_on or _init_do)
    visible_sets = {c: set(range(len(todos_conjuntos[c]))) -
                       set((hidden_modes or _init_hm).get(str(c), []))
                    for c in range(N_CONJ)}
    _recalc_mode_labels(fig, ann_map, visible_sets,
                        x_max_r, y_min_r, y_max_r,
                        fig_height=FIG_HEIGHT, x_min=x_min_r)
    _apply_legend_key(fig, dots_on or _init_do, hidden_modes or _init_hm)
    return new_lang, styles, fig, ann_map


# ── Clientside: Labels ON/OFF → plaquinhas RPM ───────────────────────────────
clientside_callback(
    """
    function(labelsOn, currentFigure, annMap, hiddenModes, dotsOn) {
        if (currentFigure === null || currentFigure === undefined) return window.dash_clientside.no_update;
        if (!annMap || Object.keys(annMap).length === 0) return window.dash_clientside.no_update;
        var fig = JSON.parse(JSON.stringify(currentFigure));
        var annotations = fig.layout.annotations || [];
        var hiddenSets = {};
        if (hiddenModes && typeof hiddenModes === 'object') {
            Object.keys(hiddenModes).forEach(function(cStr) {
                hiddenSets[cStr] = {};
                (hiddenModes[cStr] || []).forEach(function(idx) { hiddenSets[cStr][idx] = true; });
            });
        }
        Object.keys(annMap).forEach(function(group) {
            if (!group.startsWith('harm_')) return;
            var entries = annMap[group];
            entries.forEach(function(entry) {
                var ai, cE, modeIdx;
                if (Array.isArray(entry) && entry.length >= 3) { ai=entry[0]; cE=entry[1]; modeIdx=entry[2]; }
                else { ai=entry; cE=null; modeIdx=null; }
                if (ai >= annotations.length) return;
                var modeActive = (cE !== null && modeIdx !== null)
                    ? !(hiddenSets[String(cE)] && hiddenSets[String(cE)][modeIdx]) : true;
                var dotsActive = (cE !== null && dotsOn) ? (dotsOn[String(cE)] !== false) : true;
                annotations[ai].visible = labelsOn && modeActive && dotsActive;
            });
        });
        fig.layout.annotations = annotations;
        return fig;
    }
    """,
    Output('resonancia-graph', 'figure', allow_duplicate=True),
    Input('labels-on',    'data'),
    State('resonancia-graph', 'figure'),
    State('ann-map',      'data'),
    State('hidden-modes', 'data'),
    State('dots-on',      'data'),
    prevent_initial_call=True,
)

clientside_callback(
    """
    function(restyleData, currentFigure, annMap, labelsOn, dotsOn) {
        if (!restyleData || !currentFigure || !annMap) return window.dash_clientside.no_update;
        if (!labelsOn) return window.dash_clientside.no_update;
        var changes=restyleData[0]; var traceIndices=restyleData[1];
        if (!Object.prototype.hasOwnProperty.call(changes, 'visible')) return window.dash_clientside.no_update;
        var fig=JSON.parse(JSON.stringify(currentFigure));
        var annotations=fig.layout.annotations || [];
        traceIndices.forEach(function(traceIdx, i) {
            var trace=fig.data[traceIdx];
            if (!trace || !trace.legendgroup) return;
            var entries=annMap[trace.legendgroup];
            if (!entries) return;
            var newVis=Array.isArray(changes.visible)?changes.visible[i]:changes.visible;
            var shouldShow=(newVis!=='legendonly' && newVis!==false);
            entries.forEach(function(entry) {
                var ai=Array.isArray(entry)?entry[0]:entry;
                var cE=(Array.isArray(entry)&&entry.length>=3)?entry[1]:null;
                if (ai<annotations.length) {
                    var dotsActive=(cE!==null&&dotsOn)?(dotsOn[String(cE)]!==false):true;
                    annotations[ai].visible=shouldShow&&dotsActive;
                }
            });
        });
        fig.layout.annotations=annotations;
        return fig;
    }
    """,
    Output('resonancia-graph', 'figure', allow_duplicate=True),
    Input('resonancia-graph',  'restyleData'),
    State('resonancia-graph',  'figure'),
    State('ann-map',   'data'),
    State('labels-on', 'data'),
    State('dots-on',   'data'),
    prevent_initial_call=True,
)


