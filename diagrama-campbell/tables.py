# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: tables
# -----------------------------------------------------------------------------
# Constrói as tabelas HTML exibidas ABAIXO do gráfico na tela do diagrama:
#   _make_table_styles()      — retorna as tuplas de estilos base compartilhados
#                               pelas três tabelas (cabeçalho, coluna fixa,
#                               cantos, células vermelhas/verdes)
#   _build_table_conjunto(c)  — tabela detalhada de UM conjunto: harmônicas nas
#                               linhas × modos nas colunas, com Freq (Hz) e
#                               RPM crítico em cada par de células. Cor vermelha
#                               se o RPM crítico cai dentro da zona de operação
#                               (perigoso), verde se cai fora (seguro).
#   _build_table()            — versão consolidada com TODOS os conjuntos
#                               lado a lado (só aparece se N_CONJ > 1).
#   _build_table_criticos()   — tabela de Massa Efetiva Modal (MPF) por modo,
#                               com uma linha por (conjunto, modo) que tenha
#                               algum dado de MPF preenchido. X, Y, Z em cores
#                               vermelho/verde conforme superam ou não o
#                               limiar. Retorna None se nenhum modo tem MPF.
# Todas as células são não-editáveis e não-interativas (pointer-events: none).
# =============================================================================

from dash import html

from session import _g
from styles import get_visual

def _make_table_styles():
    base     = {'border': '1px solid #c8c8c8', 'whiteSpace': 'nowrap',
                'textAlign': 'center', 'userSelect': 'none', 'pointerEvents': 'none'}
    H_TH     = {**base, 'padding': '5px 10px', 'background': '#3a3a3a', 'color': 'white',
                'fontWeight': 'bold', 'fontSize': '11px',
                'position': 'sticky', 'top': '0', 'zIndex': '3', 'borderBottom': '2px solid #888'}
    H_COL    = {**base, 'padding': '5px 12px', 'background': '#f0f0f0',
                'fontWeight': 'bold', 'fontSize': '12px',
                'position': 'sticky', 'left': '0', 'zIndex': '2', 'borderRight': '2px solid #bbb'}
    H_CORNER = {**H_TH, 'left': '0', 'zIndex': '4'}
    RED      = {**base, 'padding': '4px 8px', 'background': '#ffe0e0', 'color': '#8b0000'}
    GREEN    = {**base, 'padding': '4px 8px', 'background': '#e0f5e0', 'color': '#1a5e1a'}
    return base, H_TH, H_COL, H_CORNER, RED, GREEN


def _build_table_conjunto(c):
    _, H_TH, H_COL, H_CORNER, RED, GREEN = _make_table_styles()
    todos_conjuntos = _g('todos_conjuntos', [])
    multiplicadores = _g('multiplicadores', [])
    zona_min        = _g('zona_min', 0)
    zona_max        = _g('zona_max', 0)
    vis_c = get_visual(c)
    conj  = todos_conjuntos[c]

    header = [html.Th("Harmônica", style=H_CORNER)]
    for j, f in enumerate(conj):
        header.append(html.Th(
            html.Div(f"M{j+1:02d}  ·  {f:.1f} Hz", style={'marginBottom': '2px'}),
            colSpan=2, style={**H_TH, 'background': vis_c['btn_color'], 'color': 'white'},
        ))
    subrow = [html.Th("", style=H_CORNER)]
    for _ in conj:
        subrow += [html.Th("Freq (Hz)", style={**H_TH, 'fontSize': '10px', 'background': '#555'}),
                   html.Th("RPM",       style={**H_TH, 'fontSize': '10px', 'background': '#555'})]
    rows = []
    for idx_m, m in enumerate(multiplicadores):
        cells = [html.Td(f"{m}×", style=H_COL)]
        for f in conj:
            rpm_crit = (f * 60) / m
            fill = RED if zona_min <= rpm_crit <= zona_max else GREEN
            cells.append(html.Td(f"{f:.2f}",        style=fill))
            cells.append(html.Td(f"{rpm_crit:.1f}", style=fill))
        bg = '#fafafa' if idx_m % 2 == 0 else '#f4f4f4'
        rows.append(html.Tr(cells, style={'background': bg}))
    return html.Table(
        [html.Thead([html.Tr(header), html.Tr(subrow)]), html.Tbody(rows)],
        style={'borderCollapse': 'collapse', 'minWidth': '100%',
               'pointerEvents': 'none', 'fontSize': '12px'},
    )


def _build_table():
    _, H_TH, H_COL, H_CORNER, RED, GREEN = _make_table_styles()
    todos_conjuntos = _g('todos_conjuntos', [])
    multiplicadores = _g('multiplicadores', [])
    zona_min        = _g('zona_min', 0)
    zona_max        = _g('zona_max', 0)

    header = [html.Th("Harmônica", style=H_CORNER)]
    for c, conj in enumerate(todos_conjuntos):
        vis_c = get_visual(c)
        for j, f in enumerate(conj):
            header.append(html.Th(
                [html.Div(f"M{j+1:02d} · {f:.1f} Hz", style={'marginBottom': '2px'}),
                 html.Div(vis_c['nome'], style={'fontWeight': 'normal', 'fontSize': '9px',
                                                'color': vis_c['cor_borda_plaq']})],
                colSpan=2, style=H_TH,
            ))
    rows = []
    for idx_m, m in enumerate(multiplicadores):
        cells = [html.Td(f"{m}×", style=H_COL)]
        for c, conj in enumerate(todos_conjuntos):
            for f in conj:
                rpm_crit = (f * 60) / m
                fill = RED if zona_min <= rpm_crit <= zona_max else GREEN
                cells.append(html.Td(f"{f:.2f}",        style=fill))
                cells.append(html.Td(f"{rpm_crit:.1f}", style=fill))
        bg = '#fafafa' if idx_m % 2 == 0 else '#f4f4f4'
        rows.append(html.Tr(cells, style={'background': bg}))
    return html.Table(
        [html.Thead(html.Tr(header)), html.Tbody(rows)],
        style={'borderCollapse': 'collapse', 'minWidth': '100%',
               'pointerEvents': 'none', 'fontSize': '12px'},
    )


def _build_table_criticos():
    """
    Tabela HTML agrupada por modo: uma linha por modo com MPF > limiar
    que tenha ao menos um cruzamento dentro da zona de operação.
    Colunas: Conjunto | Modo | Freq (Hz) | X (%) | Y (%) | Z (%)
    Retorna None se não há dados de MPF ou nenhum modo atende ao critério.
    """
    _, H_TH, H_COL, H_CORNER, RED, GREEN = _make_table_styles()
    todos_conjuntos = _g('todos_conjuntos', [])
    todos_mpf       = _g('todos_mpf', [])
    multiplicadores = _g('multiplicadores', [])
    zona_min        = _g('zona_min', 0)
    zona_max        = _g('zona_max', 0)

    if not todos_mpf:
        return None

    MPF_LIMIAR = _g('mpf_limiar', 5.0)

    BASE_CELL = {'border': '1px solid #c8c8c8', 'whiteSpace': 'nowrap',
                 'textAlign': 'center', 'padding': '4px 8px'}

    def _fmt(v):
        return f"{v:.1f}" if v is not None else '—'

    def _cell_mpf(v):
        """X/Y/Z: vermelho se > limiar, verde se <= limiar, cinza se None."""
        if v is None:
            return {**BASE_CELL, 'color': '#aaa'}
        if v > MPF_LIMIAR:
            return {**RED, 'fontWeight': 'bold'}
        return {**GREEN}

    def _cell_freq(xv, yv, zv):
        """Freq: vermelha se qualquer eixo > limiar; verde se todos abaixo."""
        vals = [v for v in (xv, yv, zv) if v is not None]
        if not vals:
            return BASE_CELL
        return {**RED} if any(v > MPF_LIMIAR for v in vals) else {**GREEN}

    header = html.Tr([
        html.Th("Conjunto",  style=H_CORNER),
        html.Th("Modo",      style=H_TH),
        html.Th("Freq (Hz)", style=H_TH),
        html.Th("X (%)",     style={**H_TH, 'background': '#1a5c2e'}),
        html.Th("Y (%)",     style={**H_TH, 'background': '#1a3060'}),
        html.Th("Z (%)",     style={**H_TH, 'background': '#701a30'}),
    ])

    rows = []
    for c, conj in enumerate(todos_conjuntos):
        mpf_c = todos_mpf[c] if c < len(todos_mpf) else []
        vis_c = get_visual(c)
        for i_f, f in enumerate(conj):
            mpf        = mpf_c[i_f] if i_f < len(mpf_c) else {}
            xv, yv, zv = mpf.get('x'), mpf.get('y'), mpf.get('z')
            # ignora se sem dados — qualquer modo com MPF preenchido entra
            if xv is None and yv is None and zv is None:
                continue
            rows.append(html.Tr([
                html.Td(vis_c['nome'],
                        style={**H_COL, 'color': vis_c['btn_color'],
                               'borderRight': f"3px solid {vis_c['btn_color']}"}),
                html.Td(f"M{i_f+1:02d}", style=_cell_freq(xv, yv, zv)),
                html.Td(f"{f:.2f}",      style=_cell_freq(xv, yv, zv)),
                html.Td(_fmt(xv),        style=_cell_mpf(xv)),
                html.Td(_fmt(yv),        style=_cell_mpf(yv)),
                html.Td(_fmt(zv),        style=_cell_mpf(zv)),
            ]))

    if not rows:
        return None

    return html.Table(
        [html.Thead(header), html.Tbody(rows)],
        style={'borderCollapse': 'collapse', 'minWidth': '100%',
               'pointerEvents': 'none', 'fontSize': '12px'},
    )


