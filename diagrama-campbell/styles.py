# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: styles
# -----------------------------------------------------------------------------
# Identidade visual do aplicativo e helpers de estilo reutilizáveis:
#   • estilos_harm         — 20 combinações de cor/traço/espessura para as
#                            linhas de harmônica (1×, 2×, 3×, ...)
#   • CONJUNTO_VISUAL      — paleta e ícones dos 4 conjuntos (cor da linha,
#                            das plaquinhas, dos pontos de zona/externos e
#                            das versões "translúcidas" para modos suprimidos)
#   • get_visual(c)        — acesso circular (c % 4) à paleta acima
#   • _make_ext_btn_style, _make_zona_btn_style, _make_mpf_btn_style
#                          — geradores de estilo dos botões da UI (Externos,
#                            Zona, MPF) nos estados ligado/desligado
#   • BTN_ON_STYLE, BTN_OFF_STYLE, BTN_STYLE_SMALL — botões auxiliares
#                            (Labels, + Linha, + Conjunto, etc)
#   • _tab_sel_style, _tab_unsel_style, _build_tabs_children — visual das abas
#                            "Conjunto 1..4" da tela inicial
#   • _dt_header_style, _dt_wrapper_style, _DT_STYLE_CELL, _DT_STYLE_DATA_COND
#                          — visual do DataTable de entrada das frequências
#   • _EMPTY_ROW, _FREQ_COLS, _TABS_STORE_DEFAULT — schema padrão do
#                            DataTable e do store de abas
# =============================================================================

from dash import dcc

estilos_harm = [
    dict(color='royalblue',    dash='5px,3px,2px,3px',   width=1.75),
    dict(color='forestgreen',  dash='dash',               width=2.25),
    dict(color='crimson',      dash='dot',                width=2.0),
    dict(color='purple',       dash='dashdot',            width=1.5),
    dict(color='darkorange',   dash='longdash',           width=2.25),
    dict(color='saddlebrown',  dash='8px,4px',            width=2.5),
    dict(color='teal',         dash='dash',               width=1.5),
    dict(color='deeppink',     dash='dot',                width=1.75),
    dict(color='navy',         dash='dashdot',            width=2.0),
    dict(color='goldenrod',    dash='longdash',           width=1.5),
    dict(color='darkgreen',    dash='12px,3px,2px,3px',  width=2.25),
    dict(color='steelblue',    dash='dash',               width=2.5),
    dict(color='tomato',       dash='dot',                width=1.5),
    dict(color='darkorchid',   dash='dashdot',            width=1.75),
    dict(color='chocolate',    dash='longdash',           width=2.0),
    dict(color='dodgerblue',   dash='6px,2px,2px,6px',   width=1.5),
    dict(color='olivedrab',    dash='dash',               width=1.75),
    dict(color='hotpink',      dash='dot',                width=2.5),
    dict(color='indigo',       dash='dashdot',            width=1.5),
    dict(color='sienna',       dash='longdash',           width=2.25),
]

# =====================
# IDENTIDADE VISUAL POR CONJUNTO 
# =====================
CONJUNTO_VISUAL = [
    {   # Conjunto 1 — preto / solid
        'nome': 'Conjunto 1',
        'cor_linha': 'black',         'dash_linha': 'longdash',    'width_linha': 1.5,
        'cor_bg_plaq': 'rgba(255,255,255,0.90)',
        'cor_borda_plaq': 'black',    'cor_texto_plaq': 'black',
        'cor_ponto_zona': 'crimson',  'cor_ponto_zona_linha': 'white',
        'cor_ponto_zona_t': 'rgba(180,0,0,0.12)',
        'cor_ponto_zona_linha_t': 'rgba(180,0,0,0.15)',
        'cor_ponto_ext': 'limegreen', 'cor_ponto_ext_linha': 'black',
        'cor_ponto_ext_t': 'rgba(0,200,0,0.12)',
        'cor_ponto_ext_linha_t': 'rgba(0,0,0,0.10)',
        'btn_color': '#c0392b',
    },
    {   # Conjunto 2 — amarelo escuro / dash
        'nome': 'Conjunto 2',
        'cor_linha': 'darkgoldenrod', 'dash_linha': 'dash',        'width_linha': 1.5,
        'cor_bg_plaq': 'rgba(184,134,11,0.15)',
        'cor_borda_plaq': 'darkgoldenrod', 'cor_texto_plaq': '#7a5900',
        'cor_ponto_zona': 'darkgoldenrod', 'cor_ponto_zona_linha': 'white',
        'cor_ponto_zona_t': 'rgba(184,134,11,0.12)',
        'cor_ponto_zona_linha_t': 'rgba(184,134,11,0.15)',
        'cor_ponto_ext': 'goldenrod',      'cor_ponto_ext_linha': 'saddlebrown',
        'cor_ponto_ext_t': 'rgba(218,165,32,0.12)',
        'cor_ponto_ext_linha_t': 'rgba(139,69,19,0.12)',
        'btn_color': '#b8860b',
    },
    {   # Conjunto 3 — roxo / dot
        'nome': 'Conjunto 3',
        'cor_linha': 'rebeccapurple', 'dash_linha': 'dot',         'width_linha': 1.5,
        'cor_bg_plaq': 'rgba(102,51,153,0.10)',
        'cor_borda_plaq': 'rebeccapurple', 'cor_texto_plaq': '#4a1f8a',
        'cor_ponto_zona': 'rebeccapurple', 'cor_ponto_zona_linha': 'white',
        'cor_ponto_zona_t': 'rgba(102,51,153,0.12)',
        'cor_ponto_zona_linha_t': 'rgba(102,51,153,0.15)',
        'cor_ponto_ext': 'mediumpurple',   'cor_ponto_ext_linha': 'rebeccapurple',
        'cor_ponto_ext_t': 'rgba(147,112,219,0.12)',
        'cor_ponto_ext_linha_t': 'rgba(102,51,153,0.12)',
        'btn_color': '#663399',
    },
    {   # Conjunto 4 — azul / dashdot
        'nome': 'Conjunto 4',
        'cor_linha': 'royalblue',     'dash_linha': 'dashdot',     'width_linha': 1.5,
        'cor_bg_plaq': 'rgba(65,105,225,0.10)',
        'cor_borda_plaq': 'royalblue', 'cor_texto_plaq': '#1a3a8a',
        'cor_ponto_zona': 'royalblue', 'cor_ponto_zona_linha': 'white',
        'cor_ponto_zona_t': 'rgba(65,105,225,0.12)',
        'cor_ponto_zona_linha_t': 'rgba(65,105,225,0.15)',
        'cor_ponto_ext': 'cornflowerblue', 'cor_ponto_ext_linha': 'royalblue',
        'cor_ponto_ext_t': 'rgba(100,149,237,0.12)',
        'cor_ponto_ext_linha_t': 'rgba(65,105,225,0.12)',
        'btn_color': '#4169e1',
    },
]

def get_visual(c: int) -> dict:
    return CONJUNTO_VISUAL[c % len(CONJUNTO_VISUAL)]

# ── helpers de estilo para botões (inalterado) ────────────────────────────────
def _make_ext_btn_style(is_on: bool) -> dict:
    return {
        'background': '#27ae60' if is_on else '#7f8c8d', 'color': 'white',
        'border': 'none', 'borderRadius': '5px', 'padding': '5px 10px',
        'fontSize': '12px', 'fontWeight': 'bold', 'cursor': 'pointer',
        'width': '100%', 'textAlign': 'left',
        'display': 'flex', 'alignItems': 'center', 'gap': '6px',
        'marginBottom': '2px',
    }

def _make_zona_btn_style(c: int, is_on: bool) -> dict:
    vis = get_visual(c)
    return {
        'background': vis['btn_color'] if is_on else '#7f8c8d', 'color': 'white',
        'border': 'none', 'borderRadius': '5px', 'padding': '5px 10px',
        'fontSize': '12px', 'fontWeight': 'bold', 'cursor': 'pointer',
        'width': '100%', 'textAlign': 'left',
        'display': 'flex', 'alignItems': 'center', 'gap': '6px',
        'marginBottom': '2px',
    }

BTN_ON_STYLE  = dict(
    background='#2ecc71', color='white', border='none',
    borderRadius='6px', padding='7px 18px', fontSize='13px',
    fontWeight='bold', cursor='pointer', letterSpacing='0.3px',
)
BTN_OFF_STYLE = dict(
    background='#bdc3c7', color='#555', border='none',
    borderRadius='6px', padding='7px 18px', fontSize='13px',
    fontWeight='bold', cursor='pointer', letterSpacing='0.3px',
)

def _make_mpf_btn_style(is_on: bool) -> dict:
    return {
        'background': '#2471a3' if is_on else '#7f8c8d', 'color': 'white',
        'border': 'none', 'borderRadius': '5px', 'padding': '5px 10px',
        'fontSize': '12px', 'fontWeight': 'bold', 'cursor': 'pointer',
        'width': '100%', 'textAlign': 'left',
        'display': 'flex', 'alignItems': 'center', 'gap': '6px',
        'marginBottom': '2px',
    }

def _tab_unsel_style(c: int) -> dict:
    return {
        'fontFamily': 'Arial', 'fontSize': '12px', 'fontWeight': 'bold',
        'padding': '5px 18px', 'border': '1px solid #dee2e6',
        'borderBottom': 'none', 'borderRadius': '4px 4px 0 0',
        'background': '#f0f2f5', 'color': '#495057',
        'cursor': 'pointer',
    }

def _tab_sel_style(c: int) -> dict:
    vis = get_visual(c)
    return {
        'fontFamily': 'Arial', 'fontSize': '12px', 'fontWeight': 'bold',
        'padding': '5px 18px',
        'border': f"1px solid {vis['btn_color']}",
        'borderBottom': '2px solid white',
        'borderRadius': '4px 4px 0 0',
        'background': 'white',
        'color': vis['btn_color'],
        'cursor': 'pointer',
    }

def _build_tabs_children(n: int) -> list:
    """Gera a lista de dcc.Tab para 'n' conjuntos."""
    return [
        dcc.Tab(
            label=f'Conjunto {i}',
            value=str(i),
            style=_tab_unsel_style(i - 1),
            selected_style=_tab_sel_style(i - 1),
        )
        for i in range(1, n + 1)
    ]

def _dt_wrapper_style(c: int) -> dict:
    """Estilo da borda do DataTable ativo (faixa colorida no topo)."""
    vis = get_visual(c)
    return {
        'border': '1px solid #dee2e6',
        'borderTop': f"3px solid {vis['btn_color']}",
        'borderRadius': '0 6px 6px 6px',
    }

def _dt_header_style(c: int) -> dict:
    vis = get_visual(c)
    return {
        'backgroundColor': vis['btn_color'],
        'color': 'white',
        'fontWeight': 'bold', 'textAlign': 'center', 'fontSize': '12px',
    }

# Colunas e linha vazia do DataTable de aba
_EMPTY_ROW  = {'freq': None, 'x_pct': None, 'y_pct': None, 'z_pct': None}
_FREQ_COLS  = [
    {'name': 'Frequência (Hz)', 'id': 'freq',  'editable': True},
    {'name': 'X (%)',           'id': 'x_pct', 'editable': True},
    {'name': 'Y (%)',           'id': 'y_pct', 'editable': True},
    {'name': 'Z (%)',           'id': 'z_pct', 'editable': True},
]

# Dados padrão do store de abas
_TABS_STORE_DEFAULT = {
    'n': 1,
    'active': '1',
    'rows': {str(i): [dict(_EMPTY_ROW)] * 10 for i in range(1, 5)},
}


# ── Estilos compartilhados do DataTable (movidos da seção 9/10 do monólito) ──
_DT_STYLE_CELL = {
    'fontFamily': 'Arial', 'fontSize': '13px', 'textAlign': 'center',
    'padding': '5px 10px', 'border': '1px solid #dee2e6', 'minWidth': '100px',
}
_DT_STYLE_DATA_COND = [
    {'if': {'row_index': 'odd'},  'backgroundColor': '#f8f9fa'},
    {'if': {'state': 'selected'}, 'backgroundColor': '#cfe2ff', 'border': '1px solid #0d6efd'},
]

BTN_STYLE_SMALL = dict(
    border='none', borderRadius='5px', padding='5px 12px',
    fontSize='12px', fontWeight='bold', cursor='pointer',
)
