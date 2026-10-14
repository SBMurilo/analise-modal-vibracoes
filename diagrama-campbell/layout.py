# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: layout
# -----------------------------------------------------------------------------
# Monta `app.layout`, que contém as DUAS telas do aplicativo:
#   • TELA INICIAL — cabeçalho, título da análise, Nmin/Nmax, harmônicas,
#                    limiar MPF, tolerâncias (min/max) da zona, abas dos
#                    Conjuntos 1..4 com um DataTable de entrada por aba
#                    (Freq (Hz), X%, Y%, Z% MPF), botões + Linha / + Conjunto /
#                    Remover / Limpar e o botão principal "Gerar Diagrama".
#   • TELA DO DIAGRAMA — cabeçalho com controles de eixo (X min/max, Y min/max),
#                    botão de idioma (PT/EN/ES), dropdowns ▼ Pontos / ▼ Modos /
#                    ▼ Excel (com painéis populados dinamicamente por
#                    render_dynamic_controls), botões "Labels ON/OFF",
#                    "⚠ Críticos", "← Nova Análise" e "↓ Exportar PNG",
#                    o gráfico Plotly e as tabelas de cruzamento por baixo.
# Também declara os dcc.Store globais que servem de "banco de dados" das
# interações e são compartilhados entre callbacks:
#   session-data, hidden-modes, dots-on, labels-on, ann-map, lang-store,
#   tabs-store, active-dt e alguns triggers (close-all-dropdowns).
# A importação deste módulo tem efeito colateral — DEFINE app.layout.
# =============================================================================

from dash import dcc, html, dash_table

from app_instance import app
from config import NOME_BASE
from styles import (
    BTN_ON_STYLE, BTN_STYLE_SMALL,
    _make_ext_btn_style, _make_mpf_btn_style,
    _build_tabs_children,
    _dt_wrapper_style, _dt_header_style,
    _DT_STYLE_CELL, _DT_STYLE_DATA_COND,
    _EMPTY_ROW, _FREQ_COLS, _TABS_STORE_DEFAULT,
)

app.layout = html.Div(style={'fontFamily': 'Arial'}, children=[

    # ── Stores ────────────────────────────────────────────────────────────────
    dcc.Store(id='session-data', data=None),
    dcc.Store(id='ann-map',      data={}),
    dcc.Store(id='labels-on',    data=True),
    dcc.Store(id='hidden-modes', data={}),
    dcc.Store(id='dots-on',      data={}),
    dcc.Store(id='lang-store',   data='pt'),
    # Store de abas (novo)
    dcc.Store(id='tabs-store',   data=_TABS_STORE_DEFAULT),

    # Botão invisível acionado pelo clique fora dos dropdowns
    html.Button(id='close-all-dropdowns', n_clicks=0,
                style={'display': 'none'}),

    # ══════════════════════════════════════════════════════════════════════════
    # TELA INICIAL
    # ══════════════════════════════════════════════════════════════════════════
    html.Div(id='tela-inicial', style={'display': 'block'}, children=[

        # Cabeçalho
        html.Div(style={
            'background': '#1e2a3a', 'padding': '18px 28px 14px',
            'borderBottom': '3px solid #2980b9',
        }, children=[
            html.H2(NOME_BASE,
                    style={'color': 'white', 'margin': '0 0 4px',
                           'fontSize': '20px', 'fontWeight': 'bold'}),
            html.Div("Preencha os parâmetros e as frequências naturais, depois clique em Gerar.",
                     style={'color': '#8899aa', 'fontSize': '13px'}),
        ]),

        # ── Corpo: duas colunas ───────────────────────────────────────────────
        html.Div(style={
            'display': 'flex', 'gap': '28px',
            'padding': '24px 28px 16px', 'alignItems': 'flex-start',
        }, children=[

            # ── Coluna Esquerda: Parâmetros ───────────────────────────────────
            html.Div(style={
                'width': '320px', 'flexShrink': '0',
                'background': '#f8f9fa', 'borderRadius': '8px',
                'border': '1px solid #dee2e6', 'padding': '20px',
            }, children=[
                html.H5("Parâmetros",
                        style={'margin': '0 0 18px', 'fontSize': '15px',
                               'fontWeight': 'bold', 'color': '#212529',
                               'borderBottom': '2px solid #dee2e6', 'paddingBottom': '8px'}),

                html.Div(style={'marginBottom': '14px'}, children=[
                    html.Label("Título do Diagrama",
                               style={'fontSize': '13px', 'fontWeight': 'bold',
                                      'color': '#495057', 'display': 'block',
                                      'marginBottom': '4px'}),
                    dcc.Input(id='inp-titulo', type='text', debounce=False,
                              placeholder='Ex.: Compressor de Alta Pressão',
                              style={'width': '100%', 'boxSizing': 'border-box',
                                     'fontSize': '13px', 'padding': '6px 10px',
                                     'border': '1px solid #ced4da', 'borderRadius': '5px'}),
                ]),

                html.Div(style={'marginBottom': '14px'}, children=[
                    html.Label("Nmin (rpm)",
                               style={'fontSize': '13px', 'fontWeight': 'bold',
                                      'color': '#495057', 'display': 'block',
                                      'marginBottom': '4px'}),
                    dcc.Input(id='inp-nmin', type='number', debounce=False,
                              placeholder='Ex.: 3000',
                              style={'width': '100%', 'boxSizing': 'border-box',
                                     'fontSize': '13px', 'padding': '6px 10px',
                                     'border': '1px solid #ced4da', 'borderRadius': '5px'}),
                ]),

                html.Div(style={'marginBottom': '14px'}, children=[
                    html.Label("Nmax (rpm)",
                               style={'fontSize': '13px', 'fontWeight': 'bold',
                                      'color': '#495057', 'display': 'block',
                                      'marginBottom': '4px'}),
                    dcc.Input(id='inp-nmax', type='number', debounce=False,
                              placeholder='Ex.: 5000',
                              style={'width': '100%', 'boxSizing': 'border-box',
                                     'fontSize': '13px', 'padding': '6px 10px',
                                     'border': '1px solid #ced4da', 'borderRadius': '5px'}),
                ]),

                html.Div(style={'marginBottom': '14px'}, children=[
                    html.Label("Harmônicas",
                               style={'fontSize': '13px', 'fontWeight': 'bold',
                                      'color': '#495057', 'display': 'block',
                                      'marginBottom': '4px'}),
                    dcc.Input(id='inp-harmonicas', type='text', debounce=False,
                              placeholder='Ex.: 1, 3, 5, 7',
                              style={'width': '100%', 'boxSizing': 'border-box',
                                     'fontSize': '13px', 'padding': '6px 10px',
                                     'border': '1px solid #ced4da', 'borderRadius': '5px'}),
                    html.Small("Separe por vírgula.",
                               style={'color': '#6c757d', 'fontSize': '11px'}),
                ]),

                html.Div(style={'marginBottom': '6px'}, children=[
                    html.Label("Limiar MPF (%)",
                               style={'fontSize': '13px', 'fontWeight': 'bold',
                                      'color': '#495057', 'display': 'block',
                                      'marginBottom': '4px'}),
                    dcc.Input(id='inp-mpf-limiar', type='number', debounce=False,
                              value=5, min=0, max=100, step=0.1,
                              placeholder='Ex.: 5',
                              style={'width': '100%', 'boxSizing': 'border-box',
                                     'fontSize': '13px', 'padding': '6px 10px',
                                     'border': '1px solid #ced4da', 'borderRadius': '5px'}),
                    html.Small("Participação modal acima deste valor será destacada em vermelho.",
                               style={'color': '#6c757d', 'fontSize': '11px'}),
                ]),

                html.Div(style={'marginBottom': '6px'}, children=[
                    html.Label("Tolerância da Zona de Operação (%)",
                               style={'fontSize': '13px', 'fontWeight': 'bold',
                                      'color': '#495057', 'display': 'block',
                                      'marginBottom': '4px'}),

                    html.Div(style={'display': 'flex', 'gap': '8px'}, children=[

                        html.Div(style={'flex': '1'}, children=[
                            html.Small("Mínimo (Nmin)",
                                       style={'color': '#6c757d', 'fontSize': '11px',
                                              'display': 'block', 'marginBottom': '2px'}),
                            dcc.Input(id='inp-tolerancia-min', type='number', debounce=False,
                                      value=10, min=0, max=100, step=0.1,
                                      placeholder='Ex.: 10',
                                      style={'width': '100%', 'boxSizing': 'border-box',
                                             'fontSize': '13px', 'padding': '6px 10px',
                                             'border': '1px solid #ced4da',
                                             'borderRadius': '5px'}),
                        ]),

                        html.Div(style={'flex': '1'}, children=[
                            html.Small("Máximo (Nmax)",
                                       style={'color': '#6c757d', 'fontSize': '11px',
                                              'display': 'block', 'marginBottom': '2px'}),
                            dcc.Input(id='inp-tolerancia-max', type='number', debounce=False,
                                      value=10, min=0, max=100, step=0.1,
                                      placeholder='Ex.: 10',
                                      style={'width': '100%', 'boxSizing': 'border-box',
                                             'fontSize': '13px', 'padding': '6px 10px',
                                             'border': '1px solid #ced4da',
                                             'borderRadius': '5px'}),
                        ]),
                    ]),

                    html.Small("Faixa cinza: Nmin × (1 − tol_min) até Nmax × (1 + tol_max).",
                               style={'color': '#6c757d', 'fontSize': '11px',
                                      'display': 'block', 'marginTop': '4px'}),
                ]),
            ]),

            # ── Coluna Direita: Frequências por aba ──────────────────────────
            html.Div(style={'flex': '1', 'minWidth': '0'}, children=[

                html.H5("Frequências Naturais (Hz)",
                        style={'margin': '0 0 10px', 'fontSize': '15px',
                               'fontWeight': 'bold', 'color': '#212529'}),

                # Dica de colagem
                html.Div(style={
                    'background': '#e8f4f8', 'border': '1px solid #bee5eb',
                    'borderRadius': '5px', 'padding': '8px 12px',
                    'marginBottom': '10px', 'fontSize': '12px', 'color': '#0c5460',
                }, children=[
                    "💡 Selecione os dados no Excel (sem cabeçalho), copie (Ctrl+C) e cole "
                    "diretamente nas células abaixo (Ctrl+V)."
                ]),

                # Toolbar da tabela
                html.Div(style={'marginBottom': '6px', 'display': 'flex', 'gap': '6px'}, children=[
                    html.Button("＋ Linha",      id='btn-add-row', n_clicks=0,
                                style={**BTN_STYLE_SMALL, 'background': '#6c757d', 'color': 'white'}),
                    html.Button("＋ Conjunto",   id='btn-add-col', n_clicks=0,
                                style={**BTN_STYLE_SMALL, 'background': '#6c757d', 'color': 'white'}),
                    html.Button("✕ Remover aba", id='btn-rem-col', n_clicks=0,
                                style={**BTN_STYLE_SMALL, 'background': '#6c757d', 'color': 'white'}),
                    html.Button("🗑 Limpar",      id='btn-clear',   n_clicks=0,
                                style={**BTN_STYLE_SMALL, 'background': '#dc3545', 'color': 'white'}),
                ]),

                # ── Abas estilo Excel ─────────────────────────────────────────
                dcc.Tabs(
                    id='conjunto-tabs',
                    value='1',
                    children=_build_tabs_children(1),
                    style={'marginTop': '4px'},
                    # Os estilos globais das abas são sobrescritos per-tab em
                    # _tab_unsel_style / _tab_sel_style
                    colors={'border': '#dee2e6', 'primary': '#c0392b',
                            'background': '#f0f2f5'},
                ),

                # DataTable ativo (única tabela visível, muda de conteúdo com a aba)
                html.Div(
                    id='active-dt-wrapper',
                    style=_dt_wrapper_style(0),
                    children=[
                        dash_table.DataTable(
                            id='active-dt',
                            columns=_FREQ_COLS,
                            data=[dict(_EMPTY_ROW)] * 10,
                            editable=True,
                            row_deletable=True,
                            style_table={'overflowX': 'auto'},
                            style_cell=_DT_STYLE_CELL,
                            style_header=_dt_header_style(0),
                            style_data_conditional=_DT_STYLE_DATA_COND,
                            style_as_list_view=False,
                        ),
                    ],
                ),

                html.Small("Linhas completamente vazias são ignoradas.",
                           style={'color': '#6c757d', 'fontSize': '11px',
                                  'display': 'block', 'marginTop': '6px'}),
            ]),
        ]),

        # ── Botão Gerar + Mensagem de erro ────────────────────────────────────
        html.Div(style={'padding': '0 28px 24px'}, children=[
            html.Div(id='erro-inicial',
                     style={'color': '#dc3545', 'fontSize': '13px',
                            'marginBottom': '10px', 'minHeight': '18px'}),
            html.Button(
                "🔬  Gerar Diagrama",
                id='btn-gerar', n_clicks=0,
                style={
                    'background': '#2980b9', 'color': 'white', 'border': 'none',
                    'borderRadius': '8px', 'padding': '12px 32px',
                    'fontSize': '15px', 'fontWeight': 'bold', 'cursor': 'pointer',
                    'letterSpacing': '0.5px',
                },
            ),
        ]),
    ]),

    # ══════════════════════════════════════════════════════════════════════════
    # TELA DIAGRAMA  (inalterada)
    # ══════════════════════════════════════════════════════════════════════════
    html.Div(id='tela-diagrama', style={'display': 'none'}, children=[

        html.Div([
            html.Div(style={
                'display': 'flex', 'alignItems': 'center',
                'justifyContent': 'space-between',
                'padding': '10px 20px 6px',
            }, children=[
                html.Div([
                    html.H3(id='diagrama-titulo',
                            style={'fontFamily': 'Arial', 'margin': '0',
                                   'fontSize': '18px'}),
                    html.Div(id='diagrama-subtitulo',
                             style={'fontFamily': 'Arial', 'fontSize': '13px',
                                    'color': '#555', 'marginTop': '2px'}),
                ]),
                # Seletor de idioma do gráfico
                html.Div([
                    html.Span("Idioma:", style={'fontSize': '11px', 'color': '#888',
                                                'marginRight': '4px', 'fontWeight': 'bold'}),
                    *[
                        html.Button(
                            label,
                            id={'type': 'lang-btn', 'index': code},
                            n_clicks=0,
                            style=dict(
                                background='#2980b9' if code == 'pt' else '#bdc3c7',
                                color='white', border='none',
                                borderRadius='5px', padding='4px 10px',
                                fontSize='12px', fontWeight='bold',
                                cursor='pointer', marginLeft='3px',
                            ),
                        )
                        for code, label in [('pt', '🇧🇷 PT'), ('en', '🇺🇸 EN'), ('es', '🇪🇸 ES')]
                    ],
                ], style={'display': 'flex', 'alignItems': 'center', 'marginLeft': '12px'}),
            ]),
        ]),

        html.Div([
            html.Div([
                *[
                    html.Div([
                        html.Label(label, style={'fontWeight': 'bold', 'fontSize': '13px'}),
                        dcc.Input(id=id_, type='number', value=None, step=step,
                                  debounce=True,
                                  style={'width': '115px', 'marginLeft': '6px',
                                         'fontSize': '13px', 'height': '32px'}),
                    ], style={'display': 'flex', 'alignItems': 'center', 'marginRight': '18px'})
                    for label, id_, step in [
                        ("X mín (rpm)", 'x-min', 10),
                        ("X máx (rpm)", 'x-max', 10),
                        ("Y mín (Hz)",  'y-min',  5),
                        ("Y máx (Hz)",  'y-max',  5),
                    ]
                ],
                html.Button("Labels ON", id='labels-toggle', n_clicks=0,
                            style={**BTN_ON_STYLE, 'marginRight': '8px',
                                   'height': '32px', 'padding': '0 14px'}),
                html.Div([
                    html.Button("▼ Pontos", id='pontos-dropdown-btn', n_clicks=0,
                                style=dict(background='#27ae60', color='white', border='none',
                                           borderRadius='6px', padding='0 14px', fontSize='13px',
                                           fontWeight='bold', cursor='pointer', height='32px',
                                           marginRight='4px')),
                    html.Div(id='pontos-dropdown-panel', children=[
                        html.Button("● Externos (verde)", id='green-ext-toggle', n_clicks=0,
                                    style=_make_ext_btn_style(True)),
                        html.Button("◆ Pontos MPF", id='mpf-vivid-toggle', n_clicks=0,
                                    style=_make_mpf_btn_style(False)),
                        html.Hr(style={'margin': '4px 0', 'border': 'none',
                                       'borderTop': '1px solid #eee'}),
                        html.Div(id='zona-buttons-container'),
                    ], style={
                        'display': 'none', 'position': 'absolute', 'zIndex': 9999,
                        'top': '36px', 'left': '0', 'background': 'white',
                        'border': '1px solid #ccc', 'borderRadius': '6px',
                        'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
                        'padding': '6px', 'minWidth': '190px',
                    }),
                ], style={'position': 'relative', 'display': 'inline-block'}),
                html.Div([
                    html.Button("▼ Modos", id='modos-dropdown-btn', n_clicks=0,
                                style=dict(background='#555', color='white', border='none',
                                           borderRadius='6px', padding='0 14px', fontSize='13px',
                                           fontWeight='bold', cursor='pointer', height='32px',
                                           marginLeft='4px')),
                    html.Div(id='modos-dropdown-panel', children=[
                        html.Div(id='modos-panel-content'),
                    ], style={
                        'display': 'none', 'position': 'absolute', 'zIndex': 9999,
                        'top': '36px', 'left': '0', 'background': 'white',
                        'border': '1px solid #ccc', 'borderRadius': '6px',
                        'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
                        'padding': '4px 0', 'minWidth': '180px',
                        'maxHeight': '420px', 'overflowY': 'auto',
                    }),
                ], style={'position': 'relative', 'display': 'inline-block'}),
                html.Button("⚠ Críticos", id='btn-criticos', n_clicks=0,
                            style=dict(background='#e67e22', color='white', border='none',
                                       borderRadius='6px', padding='0 14px', fontSize='13px',
                                       fontWeight='bold', cursor='pointer', height='32px',
                                       marginLeft='4px')),
            ], style={'display': 'flex', 'alignItems': 'center',
                      'flexWrap': 'wrap', 'gap': '4px', 'flex': '1'}),

            html.Div(style={'width': '1px', 'background': '#bbb',
                            'alignSelf': 'stretch', 'margin': '0 12px'}),

            html.Div([
                html.Button(
                    "← Nova Análise",
                    id='btn-nova-analise', n_clicks=0,
                    style=dict(background='#6c757d', color='white', border='none',
                               borderRadius='6px', padding='0 16px', fontSize='13px',
                               fontWeight='bold', cursor='pointer', height='32px',
                               marginRight='8px')),
                html.Button("⬇ Exportar PNG", id='export-btn', n_clicks=0,
                            style=dict(background='#2980b9', color='white', border='none',
                                       borderRadius='6px', padding='0 16px', fontSize='13px',
                                       fontWeight='bold', cursor='pointer', height='32px',
                                       marginRight='8px')),
                html.Div([
                    html.Button("📊 Relatório Excel ▼", id='excel-dropdown-btn', n_clicks=0,
                                style=dict(background='#27ae60', color='white', border='none',
                                           borderRadius='6px', padding='0 14px', fontSize='13px',
                                           fontWeight='bold', cursor='pointer', height='32px')),
                    html.Div(id='excel-dropdown-panel', children=[
                        html.Div(id='excel-buttons-container'),
                        html.Hr(style={'margin': '4px 0', 'border': 'none',
                                       'borderTop': '1px solid #eee'}),
                        html.Button("📊 Tabela MPF",
                                    id={'type': 'excel-export-btn', 'index': -2},
                                    n_clicks=0,
                                    style={'background': '#b8860b', 'color': 'white',
                                           'border': 'none', 'borderRadius': '5px',
                                           'padding': '5px 10px', 'fontSize': '12px',
                                           'fontWeight': 'bold', 'cursor': 'pointer',
                                           'width': '100%', 'textAlign': 'left',
                                           'marginBottom': '2px'}),
                        html.Button("  Completo",
                                    id={'type': 'excel-export-btn', 'index': -1},
                                    n_clicks=0,
                                    style={'background': '#555', 'color': 'white',
                                           'border': 'none', 'borderRadius': '5px',
                                           'padding': '5px 10px', 'fontSize': '12px',
                                           'fontWeight': 'bold', 'cursor': 'pointer',
                                           'width': '100%', 'textAlign': 'left'}),
                    ], style={
                        'display': 'none', 'position': 'absolute', 'zIndex': 9999,
                        'top': '36px', 'right': '0', 'background': 'white',
                        'border': '1px solid #ccc', 'borderRadius': '6px',
                        'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
                        'padding': '6px', 'minWidth': '160px',
                    }),
                ], style={'position': 'relative', 'display': 'inline-block'}),
            ], style={'display': 'flex', 'alignItems': 'center',
                      'gap': '8px', 'flexShrink': '0'}),

        ], style={
            'display': 'flex', 'alignItems': 'center',
            'padding': '8px 20px', 'backgroundColor': '#f0f0f0',
            'borderRadius': '8px', 'margin': '4px 20px 8px',
        }),

        dcc.Graph(id='resonancia-graph', style={'margin': '0 10px'}),
        html.Div(id='export-status', style={
            'fontFamily': 'Arial', 'fontSize': '12px',
            'padding': '2px 20px 8px', 'color': '#27ae60', 'minHeight': '18px',
        }),

        html.Div(id='tabelas-cruzamento',
                 style={'margin': '10px 20px 20px', 'fontFamily': 'Arial', 'fontSize': '12px'}),
    ]),
])

