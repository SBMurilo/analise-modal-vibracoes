"""
Explorador de Análise Modal
----------------------------
Visualiza Massa Efetiva, MPF e Amortecimento por direção.
Baseado nos conceitos de Irvine (2012).

Instalação:
    pip install dash plotly pandas pywebview

Uso:
    python explorador_modal.py
"""

import threading
import time
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import webview

# ==============================================================
# DADOS — substitua pelos seus valores reais
# ==============================================================

MODOS = pd.DataFrame([
    {"Modo": "Modo_1", "Freq_Hz": 45.2,  "Meff_X": 82.5, "Meff_Y": 1.2,  "Meff_Z": 0.0 },
    {"Modo": "Modo_2", "Freq_Hz": 110.0, "Meff_X": 0.5,  "Meff_Y": 75.0, "Meff_Z": 2.1 },
    {"Modo": "Modo_3", "Freq_Hz": 325.0, "Meff_X": 0.0,  "Meff_Y": 0.1,  "Meff_Z": 91.0},
    {"Modo": "Modo_4", "Freq_Hz": 420.0, "Meff_X": 1.2,  "Meff_Y": 0.8,  "Meff_Z": 0.5 },
])

# ==============================================================
# HELPERS
# ==============================================================

def get_coluna_direcao(direcao: str) -> str:
    return f"Meff_{direcao}"


def calcular_daf(zeta_pct: float) -> float:
    return 1.0 / (2.0 * zeta_pct / 100.0)


def classificar_risco(meff_pct: float, daf: float) -> str:
    if meff_pct >= 50 and daf > 20:
        return "ALTO"
    if meff_pct >= 15 and daf > 10:
        return "MÉDIO"
    return "BAIXO"


def cor_barra(pct: float) -> str:
    if pct >= 50:
        return "#e24b4a"
    if pct >= 15:
        return "#ef9f27"
    return "#888780"


# ==============================================================
# FIGURAS
# ==============================================================

def figura_barras_massa(direcao: str) -> go.Figure:
    col = get_coluna_direcao(direcao)
    df  = MODOS.sort_values(col, ascending=True).copy()
    df["Acumulado"] = df[col].sum()

    cores  = [cor_barra(v) for v in df[col]]
    total  = df[col].sum()
    acum   = df[col].sort_values(ascending=False).cumsum().values

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df["Modo"],
        x=df[col],
        orientation="h",
        marker_color=cores,
        text=[f"{v:.1f}%" for v in df[col]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Massa Ef. %{x:.1f}%<extra></extra>",
        name="Massa Efetiva",
    ))

    fig.add_vline(
        x=90,
        line_dash="dash",
        line_color="#f39c12",
        line_width=2,
        annotation_text="90%",
        annotation_font_color="#f39c12",
        annotation_position="top",
    )

    status = "✓ Critério 90% atendido" if total >= 90 else f"⚠ Soma = {total:.1f}% — abaixo de 90%"
    cor_status = "#2ecc71" if total >= 90 else "#e74c3c"

    fig.update_layout(
        title=dict(
            text=f"Massa Efetiva — Direção {direcao}    <span style='color:{cor_status};font-size:13px'>{status}</span>",
            font_size=14,
        ),
        xaxis=dict(title="Massa Efetiva (%)", range=[0, 115]),
        yaxis=dict(title=""),
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font_color="#c9d1d9",
        margin=dict(l=80, r=40, t=60, b=40),
        height=280,
        showlegend=False,
    )
    return fig


def figura_acumulada(direcao: str) -> go.Figure:
    col = get_coluna_direcao(direcao)
    df  = MODOS.sort_values(col, ascending=False).copy()
    df["Acum"] = df[col].cumsum()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=list(range(1, len(df) + 1)),
        y=df["Acum"].values,
        mode="lines+markers",
        line=dict(color="#3498db", width=2),
        marker=dict(size=9, color="#3498db"),
        text=df["Modo"].values,
        hovertemplate="<b>%{text}</b><br>Acumulado: %{y:.1f}%<extra></extra>",
        name="Acumulado",
    ))

    fig.add_hline(
        y=90,
        line_dash="dash",
        line_color="#f39c12",
        line_width=2,
        annotation_text="90%",
        annotation_font_color="#f39c12",
        annotation_position="right",
    )

    fig.update_layout(
        title=dict(text=f"Massa Acumulada — Direção {direcao}", font_size=14),
        xaxis=dict(
            title="Nº de modos incluídos",
            tickvals=list(range(1, len(df) + 1)),
            ticktext=df["Modo"].values,
        ),
        yaxis=dict(title="Massa Acumulada (%)", range=[0, 110]),
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font_color="#c9d1d9",
        margin=dict(l=60, r=40, t=50, b=60),
        height=260,
        showlegend=False,
    )
    return fig


def figura_daf(modo_idx: int, zeta_pct: float, direcao: str) -> go.Figure:
    col   = get_coluna_direcao(direcao)
    modo  = MODOS.iloc[modo_idx]
    meff  = float(modo[col])
    daf   = calcular_daf(zeta_pct)
    risco = classificar_risco(meff, daf)
    cor_risco = {"ALTO": "#e74c3c", "MÉDIO": "#f39c12", "BAIXO": "#2ecc71"}[risco]

    zetas = [i * 0.5 for i in range(1, 21)]
    dafs  = [calcular_daf(z) for z in zetas]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=zetas,
        y=dafs,
        mode="lines",
        line=dict(color="#3498db", width=2),
        name="DAF",
        hovertemplate="ζ = %{x:.1f}%<br>DAF = %{y:.1f}×<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=[zeta_pct],
        y=[daf],
        mode="markers",
        marker=dict(size=14, color=cor_risco, symbol="circle",
                    line=dict(color="white", width=2)),
        name=f"ζ = {zeta_pct:.1f}%",
        hovertemplate=f"<b>{modo['Modo']}</b><br>ζ = {zeta_pct:.1f}%<br>DAF = {daf:.1f}×<extra></extra>",
    ))

    fig.add_annotation(
        x=zeta_pct, y=daf,
        text=f" DAF = {daf:.0f}×<br> Risco: {risco}",
        showarrow=True,
        arrowhead=2,
        arrowcolor=cor_risco,
        font=dict(color=cor_risco, size=12),
        bgcolor="#0d1117",
        bordercolor=cor_risco,
        borderwidth=1,
        ax=60, ay=-40,
    )

    fig.update_layout(
        title=dict(
            text=f"Amortecimento × DAF — {modo['Modo']} | Meff {direcao} = {meff:.1f}%",
            font_size=14,
        ),
        xaxis=dict(title="Amortecimento ζ (%)"),
        yaxis=dict(title="DAF = 1 / 2ζ"),
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font_color="#c9d1d9",
        margin=dict(l=60, r=40, t=60, b=50),
        height=280,
        showlegend=False,
    )
    return fig


def figura_radar(direcao: str) -> go.Figure:
    col = get_coluna_direcao(direcao)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=MODOS["Modo"],
        y=MODOS[col],
        marker_color=[cor_barra(v) for v in MODOS[col]],
        text=[f"{v:.1f}%" for v in MODOS[col]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
    ))

    fig.add_hline(
        y=15,
        line_dash="dot",
        line_color="#888780",
        annotation_text="relevante",
        annotation_font_color="#888780",
        annotation_position="right",
    )

    fig.update_layout(
        title=dict(text=f"Comparação entre modos — Direção {direcao}", font_size=14),
        xaxis_title="Modo",
        yaxis=dict(title="Massa Efetiva (%)", range=[0, 110]),
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font_color="#c9d1d9",
        margin=dict(l=50, r=40, t=60, b=50),
        height=260,
        showlegend=False,
    )
    return fig


# ==============================================================
# APP DASH
# ==============================================================

app = dash.Dash(__name__, title="Explorador Modal")

app.layout = html.Div(style={
    "backgroundColor": "#0d1117",
    "minHeight": "100vh",
    "padding": "24px",
    "fontFamily": "Consolas, monospace",
    "color": "#c9d1d9",
}, children=[

    # Cabeçalho
    html.Div([
        html.H1("Explorador de análise modal",
                style={"fontSize": "20px", "color": "#58a6ff",
                       "margin": "0 0 4px 0", "fontWeight": "500"}),
        html.P("Massa Efetiva · Critério dos 90% · DAF por amortecimento",
               style={"color": "#8b949e", "fontSize": "12px", "margin": 0}),
    ], style={"marginBottom": "20px", "borderBottom": "1px solid #21262d",
              "paddingBottom": "14px"}),

    # Controles
    html.Div(style={
        "display": "grid",
        "gridTemplateColumns": "auto auto 1fr auto",
        "gap": "16px",
        "alignItems": "center",
        "marginBottom": "20px",
        "padding": "14px 18px",
        "backgroundColor": "#161b22",
        "border": "1px solid #21262d",
        "borderRadius": "8px",
    }, children=[

        html.Div([
            html.P("Direção de excitação",
                   style={"fontSize": "11px", "color": "#8b949e",
                          "margin": "0 0 6px 0", "letterSpacing": "0.06em"}),
            dcc.RadioItems(
                id="radio-direcao",
                options=[{"label": d, "value": d} for d in ["X", "Y", "Z"]],
                value="X",
                inline=True,
                inputStyle={"marginRight": "4px", "accentColor": "#58a6ff"},
                labelStyle={"marginRight": "14px", "fontSize": "14px",
                            "color": "#c9d1d9"},
            ),
        ]),

        html.Div([
            html.P("Modo para análise DAF",
                   style={"fontSize": "11px", "color": "#8b949e",
                          "margin": "0 0 6px 0", "letterSpacing": "0.06em"}),
            dcc.Dropdown(
                id="drop-modo",
                options=[{"label": row["Modo"], "value": i}
                         for i, row in MODOS.iterrows()],
                value=0,
                clearable=False,
                style={"width": "140px", "fontSize": "13px",
                       "backgroundColor": "#0d1117", "color": "#c9d1d9"},
            ),
        ]),

        html.Div([
            html.P(["Amortecimento ζ: ",
                    html.Span(id="zeta-label",
                              style={"color": "#58a6ff", "fontWeight": "500"}),
                    " %"],
                   style={"fontSize": "11px", "color": "#8b949e",
                          "margin": "0 0 6px 0", "letterSpacing": "0.06em"}),
            dcc.Slider(
                id="slider-zeta",
                min=0.5, max=10, step=0.5, value=2.0,
                marks={1: "1%", 3: "3%", 5: "5%", 10: "10%"},
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ]),

        html.Div(id="card-risco", style={"textAlign": "center"}),
    ]),

    # Gráficos — linha 1
    html.Div(style={
        "display": "grid",
        "gridTemplateColumns": "1fr 1fr",
        "gap": "12px",
        "marginBottom": "12px",
    }, children=[
        html.Div([dcc.Graph(id="graf-barras",   config={"displayModeBar": False})],
                 style={"backgroundColor": "#161b22", "border": "1px solid #21262d",
                        "borderRadius": "8px", "padding": "4px"}),
        html.Div([dcc.Graph(id="graf-acumulada", config={"displayModeBar": False})],
                 style={"backgroundColor": "#161b22", "border": "1px solid #21262d",
                        "borderRadius": "8px", "padding": "4px"}),
    ]),

    # Gráficos — linha 2
    html.Div(style={
        "display": "grid",
        "gridTemplateColumns": "1fr 1fr",
        "gap": "12px",
    }, children=[
        html.Div([dcc.Graph(id="graf-daf",   config={"displayModeBar": False})],
                 style={"backgroundColor": "#161b22", "border": "1px solid #21262d",
                        "borderRadius": "8px", "padding": "4px"}),
        html.Div([dcc.Graph(id="graf-radar", config={"displayModeBar": False})],
                 style={"backgroundColor": "#161b22", "border": "1px solid #21262d",
                        "borderRadius": "8px", "padding": "4px"}),
    ]),

    html.P("Irvine, T. (2012) · Chopra, A.K. (2001) · ASCE 7-22 §12.9",
           style={"textAlign": "center", "fontSize": "10px",
                  "color": "#484f58", "marginTop": "16px"}),
])


# ==============================================================
# CALLBACKS
# ==============================================================

@app.callback(
    Output("graf-barras",   "figure"),
    Output("graf-acumulada","figure"),
    Output("graf-daf",      "figure"),
    Output("graf-radar",    "figure"),
    Output("zeta-label",    "children"),
    Output("card-risco",    "children"),
    Input("radio-direcao",  "value"),
    Input("drop-modo",      "value"),
    Input("slider-zeta",    "value"),
)
def atualizar(direcao, modo_idx, zeta):
    col   = get_coluna_direcao(direcao)
    meff  = float(MODOS.iloc[modo_idx][col])
    daf   = calcular_daf(zeta)
    risco = classificar_risco(meff, daf)

    cor_risco = {"ALTO": "#e74c3c", "MÉDIO": "#f39c12", "BAIXO": "#2ecc71"}[risco]
    bg_risco  = {"ALTO": "rgba(231,76,60,0.12)",
                 "MÉDIO": "rgba(243,156,18,0.12)",
                 "BAIXO": "rgba(46,204,113,0.12)"}[risco]

    card = html.Div([
        html.Div("risco",
                 style={"fontSize": "10px", "color": "#8b949e",
                        "letterSpacing": "0.08em"}),
        html.Div(risco,
                 style={"fontSize": "18px", "fontWeight": "500",
                        "color": cor_risco}),
    ], style={
        "backgroundColor": bg_risco,
        "border": f"1px solid {cor_risco}",
        "borderRadius": "8px",
        "padding": "10px 20px",
        "minWidth": "90px",
    })

    return (
        figura_barras_massa(direcao),
        figura_acumulada(direcao),
        figura_daf(modo_idx, zeta, direcao),
        figura_radar(direcao),
        f"{zeta:.1f}",
        card,
    )


# ==============================================================
# MAIN — abre em janela nativa (sem navegador)
# ==============================================================

def rodar_dash():
    app.run(debug=False, port=8050, use_reloader=False)


if __name__ == "__main__":
    t = threading.Thread(target=rodar_dash, daemon=True)
    t.start()
    time.sleep(1.5)

    webview.create_window(
        title="Explorador de Análise Modal",
        url="http://127.0.0.1:8050",
        width=1280,
        height=820,
        resizable=True,
        min_size=(900, 600),
    )
    webview.start()
