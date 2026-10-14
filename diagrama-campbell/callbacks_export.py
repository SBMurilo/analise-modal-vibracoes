# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: callbacks_export
# -----------------------------------------------------------------------------
# Exportação e listeners globais clientside:
#   exportar_png       — botão "↓ Exportar PNG": grava PASTA_GRAFICOS/
#                        Diagrama-<titulo>.png via kaleido em alta resolução
#                        (scale=3, 1600×900); se o arquivo já existir, gera
#                        automaticamente um sufixo _NNN. Retorna uma
#                        mensagem de status para o rodapé da tela.
#   exportar_excel     — botões "  Conjunto N" do menu Excel: gera um
#                        arquivo .xlsx por conjunto contendo abas de dados
#                        (frequências, harmônicas, RPMs críticos e valores
#                        MPF), com formatação por cor/fonte via openpyxl.
#   [clientside] resize — instala UM listener global de resize da janela que
#                        dispara change nos inputs x-max/y-max a cada 400 ms,
#                        forçando o Plotly a recalcular dimensões do gráfico.
#   [clientside] outside-click — instala UM listener global que fecha os
#                        dropdowns ▼ Pontos / ▼ Modos / ▼ Excel quando o
#                        usuário clica em qualquer lugar fora deles.
# =============================================================================

import json
import plotly.graph_objects as go
import plotly.io as pio

from dash import (callback, Input, Output, State, no_update, ALL, callback_context)
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app_instance import app
from config  import PASTA_GRAFICOS
from session import _SESSION, _g
from styles  import get_visual

@callback(
    Output('export-status', 'children'),
    Input('export-btn', 'n_clicks'),
    State('resonancia-graph', 'figure'),
    prevent_initial_call=True,
)
def exportar_png(n_clicks, figure_state):
    if not figure_state or not _SESSION:
        return "Erro: nenhuma figura disponível."
    titulo_arquivo = _g('titulo_arquivo', 'diagrama')
    pasta = PASTA_GRAFICOS;  pasta.mkdir(parents=True, exist_ok=True)
    base  = pasta / f"Diagrama-{titulo_arquivo}.png"
    caminho = base if not base.exists() else None
    if caminho is None:
        i = 2
        while True:
            caminho = pasta / f"Diagrama-{titulo_arquivo}_{i:03d}.png"
            if not caminho.exists(): break
            i += 1
    fig = go.Figure(figure_state)
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white',
                      width=1600, height=900,
                      legend=dict(orientation="h", yanchor="top", y=-0.10,
                                  xanchor='center', x=0.5),
                      margin=dict(r=90, t=60, b=80))
    try:
        pio.write_image(fig, str(caminho), format='png', scale=3, width=1600, height=900)
        return f"✔ PNG salvo: {caminho}"
    except Exception as e:
        return f"✖ Erro ao exportar: {e}  (pip install kaleido)"


@callback(
    Output('export-status',        'children', allow_duplicate=True),
    Output('excel-dropdown-panel', 'style',    allow_duplicate=True),
    Input({'type': 'excel-export-btn', 'index': ALL}, 'n_clicks'),
    State('excel-dropdown-panel', 'style'),
    prevent_initial_call=True,
)
def exportar_excel(n_clicks_list, panel_style):
    ctx = callback_context
    if not ctx.triggered or not _SESSION:
        return no_update, no_update
    try:
        prop_id = ctx.triggered[0]['prop_id']
        btn_id  = json.loads(prop_id.rsplit('.', 1)[0])
        idx     = int(btn_id['index'])
    except Exception:
        return no_update, no_update
    if not ctx.triggered[0].get('value'):
        return no_update, no_update

    closed_style = dict(panel_style or {}); closed_style['display'] = 'none'

    todos_conjuntos = _g('todos_conjuntos', [])
    multiplicadores = _g('multiplicadores', [])
    zona_min        = _g('zona_min', 0)
    zona_max        = _g('zona_max', 0)
    n_min           = _g('n_min', 0)
    n_max           = _g('n_max', 0)
    titulo_usuario  = _g('titulo_usuario', '')
    titulo_arquivo  = _g('titulo_arquivo', 'relatorio')
    N_CONJ          = _g('N_CONJ', 0)

    if idx == -2:
        # ── Exportação exclusiva da Tabela MPF ───────────────────────────────
        todos_mpf      = _g('todos_mpf', [])
        titulo_arquivo = _g('titulo_arquivo', 'relatorio')
        titulo_usuario = _g('titulo_usuario', '')
        MPF_LIMIAR     = _g('mpf_limiar', 5.0)

        pasta = PASTA_GRAFICOS; pasta.mkdir(parents=True, exist_ok=True)
        base  = pasta / f"Tabela_MPF_{titulo_arquivo}.xlsx"
        caminho = base if not base.exists() else None
        if caminho is None:
            i = 2
            while True:
                caminho = pasta / f"Tabela_MPF_{titulo_arquivo}_{i:03d}.xlsx"
                if not caminho.exists(): break
                i += 1

        FILL_RED        = PatternFill("solid", fgColor="FF9999")
        FILL_GREEN      = PatternFill("solid", fgColor="CCFFCC")
        FILL_NEUTRAL    = PatternFill("solid", fgColor="F2F2F2")
        FILL_YELLOW_HDR = PatternFill("solid", fgColor="F0C040")
        FONT_BOLD       = Font(bold=True)
        FONT_TITLE      = Font(bold=True, size=12)
        ALIGN_C         = Alignment(horizontal='center', vertical='center')
        ALIGN_L         = Alignment(horizontal='left',   vertical='center')

        def thin_border_mpf():
            s = Side(style='thin')
            return Border(left=s, right=s, top=s, bottom=s)

        def _fill_mpf(v):
            if v is None: return FILL_NEUTRAL
            return FILL_RED if v > MPF_LIMIAR else FILL_GREEN

        def _fill_freq(xv, yv, zv):
            vals = [v for v in (xv, yv, zv) if v is not None]
            if not vals: return FILL_NEUTRAL
            return FILL_RED if any(v > MPF_LIMIAR for v in vals) else FILL_GREEN

        wb2  = Workbook()
        ws_m = wb2.active
        ws_m.title = "Massa Efetiva Modal"

        ws_m.merge_cells("A1:F1")
        ws_m["A1"].value     = f"Massa Efetiva Modal por Modo — {titulo_usuario}"
        ws_m["A1"].font      = FONT_TITLE
        ws_m["A1"].alignment = ALIGN_L

        hdrs = ["Conjunto", "Modo", "Freq (Hz)", "X (%)", "Y (%)", "Z (%)"]
        for col_i, h in enumerate(hdrs, start=1):
            cell            = ws_m.cell(2, col_i, h)
            cell.font       = FONT_BOLD
            cell.fill       = FILL_YELLOW_HDR
            cell.alignment  = ALIGN_C
            cell.border     = thin_border_mpf()

        row_cur = 3
        has_any = False
        for c_idx, conj in enumerate(todos_conjuntos):
            mpf_c = todos_mpf[c_idx] if todos_mpf and c_idx < len(todos_mpf) else []
            vis_c = get_visual(c_idx)
            for i_f, f_nat in enumerate(conj):
                mpf        = mpf_c[i_f] if i_f < len(mpf_c) else {}
                xv, yv, zv = mpf.get('x'), mpf.get('y'), mpf.get('z')
                if xv is None and yv is None and zv is None:
                    continue
                valores = [
                    vis_c['nome'],
                    f"M{i_f+1:02d}",
                    round(f_nat, 2),
                    round(xv, 1) if xv is not None else "—",
                    round(yv, 1) if yv is not None else "—",
                    round(zv, 1) if zv is not None else "—",
                ]
                fills = [
                    None,                         # Conjunto — sem fill especial
                    _fill_freq(xv, yv, zv),       # Modo
                    _fill_freq(xv, yv, zv),       # Freq
                    _fill_mpf(xv),                # X
                    _fill_mpf(yv),                # Y
                    _fill_mpf(zv),                # Z
                ]
                for col_i, (val, fill) in enumerate(zip(valores, fills), start=1):
                    cell            = ws_m.cell(row_cur, col_i, val)
                    cell.alignment  = ALIGN_C
                    cell.border     = thin_border_mpf()
                    if fill is not None:
                        cell.fill = fill
                row_cur += 1
                has_any  = True

        if not has_any:
            ws_m["A3"].value = "Nenhum dado de MPF encontrado."
            ws_m["A3"].font  = Font(italic=True)

        for col_i, w in enumerate([20, 8, 11, 8, 8, 8], start=1):
            ws_m.column_dimensions[get_column_letter(col_i)].width = w
        ws_m.row_dimensions[1].height = 18

        try:
            wb2.save(str(caminho))
            return f"✔ Tabela MPF salva: {caminho}", closed_style
        except Exception as e:
            return f"✖ Erro Excel: {e}  (pip install openpyxl)", closed_style

    if idx == -1:
        conjuntos_rel = list(range(N_CONJ)); sufixo = "Completo"
    else:
        conjuntos_rel = [idx]; sufixo = get_visual(idx)['nome'].replace(' ', '')

    pasta = PASTA_GRAFICOS; pasta.mkdir(parents=True, exist_ok=True)
    base  = pasta / f"Relatorio-{titulo_arquivo}-{sufixo}.xlsx"
    caminho = base if not base.exists() else None
    if caminho is None:
        i = 2
        while True:
            caminho = pasta / f"Relatorio-{titulo_arquivo}-{sufixo}_{i:03d}.xlsx"
            if not caminho.exists(): break
            i += 1

    FILL_RED    = PatternFill("solid", fgColor="FF9999")
    FILL_GREEN  = PatternFill("solid", fgColor="CCFFCC")
    FILL_HEADER = PatternFill("solid", fgColor="D9D9D9")
    FILL_SUBHDR = PatternFill("solid", fgColor="F2F2F2")
    FONT_BOLD   = Font(bold=True)
    FONT_TITLE  = Font(bold=True, size=12)
    ALIGN_C     = Alignment(horizontal='center', vertical='center')
    ALIGN_L     = Alignment(horizontal='left',   vertical='center')

    def thin_border():
        s = Side(style='thin')
        return Border(left=s, right=s, top=s, bottom=s)

    def apply_header(cell, text, fill=FILL_HEADER):
        cell.value=text; cell.font=FONT_BOLD; cell.fill=fill
        cell.alignment=ALIGN_C; cell.border=thin_border()

    wb = Workbook(); ws = wb.active; ws.title = "Cruzamentos"
    conjs_data      = [(c, todos_conjuntos[c]) for c in conjuntos_rel]
    total_data_cols = sum(len(conj) for _, conj in conjs_data) * 2

    ws.merge_cells(f"A1:{get_column_letter(1+total_data_cols)}1")
    ws["A1"].value=f"Diagrama de Frequências Naturais X Excitações — {titulo_usuario}  [{sufixo}]"
    ws["A1"].font=FONT_TITLE; ws["A1"].alignment=ALIGN_L
    ws["A2"]=(f"Nmin: {n_min:.0f} rpm   Nmax: {n_max:.0f} rpm"
              f"   Zona: {zona_min:.0f}–{zona_max:.0f} rpm")
    ws["A2"].alignment=ALIGN_L
    ws.merge_cells(f"A2:{get_column_letter(1+total_data_cols)}2")

    ROW_HDR=3
    ws.cell(ROW_HDR,1,"Harmônica").font=FONT_BOLD
    ws.cell(ROW_HDR,1).fill=FILL_HEADER; ws.cell(ROW_HDR,1).alignment=ALIGN_C
    ws.cell(ROW_HDR,1).border=thin_border()
    col_cur=2
    for c, conj in conjs_data:
        vis_c=get_visual(c)
        for j, f_nat in enumerate(conj):
            label=(f"M{j+1:02d} ({f_nat:.1f} Hz)"
                   +(f" — {vis_c['nome']}" if len(conjuntos_rel)>1 else ""))
            ws.merge_cells(start_row=ROW_HDR,start_column=col_cur,end_row=ROW_HDR,end_column=col_cur+1)
            cell=ws.cell(ROW_HDR,col_cur,label); cell.font=FONT_BOLD; cell.fill=FILL_HEADER
            cell.alignment=ALIGN_C; cell.border=thin_border()
            ws.cell(ROW_HDR,col_cur+1).border=thin_border()
            col_cur+=2

    ROW_SUB=4
    ws.cell(ROW_SUB,1,"").fill=FILL_SUBHDR; ws.cell(ROW_SUB,1).border=thin_border()
    col_cur=2
    for _,conj in conjs_data:
        for _ in conj:
            apply_header(ws.cell(ROW_SUB,col_cur),"Freq (Hz)",FILL_SUBHDR)
            apply_header(ws.cell(ROW_SUB,col_cur+1),"RPM",FILL_SUBHDR)
            col_cur+=2

    for i_m,m in enumerate(multiplicadores):
        row=5+i_m; cell=ws.cell(row,1,f"{m}×")
        cell.font=FONT_BOLD; cell.alignment=ALIGN_C; cell.border=thin_border()
        col_cur=2
        for _,conj in conjs_data:
            for f_nat in conj:
                rpm_crit=(f_nat*60)/m
                fill=FILL_RED if zona_min<=rpm_crit<=zona_max else FILL_GREEN
                cf=ws.cell(row,col_cur,round(f_nat,2)); cr=ws.cell(row,col_cur+1,round(rpm_crit,1))
                for cell_ in (cf,cr):
                    cell_.fill=fill; cell_.alignment=ALIGN_C; cell_.border=thin_border()
                col_cur+=2

    ws.column_dimensions['A'].width=12; col_cur=2
    for _,conj in conjs_data:
        for _ in conj:
            ws.column_dimensions[get_column_letter(col_cur)].width=11
            ws.column_dimensions[get_column_letter(col_cur+1)].width=11
            col_cur+=2
    ws.row_dimensions[1].height=20; ws.row_dimensions[2].height=16

    # ── Aba de Pontos Críticos MPF ────────────────────────────────────────────
    todos_mpf  = _g('todos_mpf', [])
    MPF_LIMIAR = _g('mpf_limiar', 5.0)

    if todos_mpf:
        ws2 = wb.create_sheet("Pontos Críticos MPF")
        FILL_ORANGE = PatternFill("solid", fgColor="FFF3CD")
        FILL_YELLOW_HDR = PatternFill("solid", fgColor="F0C040")

        # título
        ws2.merge_cells("A1:I1")
        ws2["A1"].value = (f"Pontos Críticos MPF (eixo > {MPF_LIMIAR:.0f}%) — "
                           f"{titulo_usuario}")
        ws2["A1"].font = FONT_TITLE; ws2["A1"].alignment = ALIGN_L

        # cabeçalho
        hdrs = ["Conjunto", "Modo", "Freq (Hz)", "Harmônica",
                "RPM Crítico", "X (%)", "Y (%)", "Z (%)"]
        for col_i, h in enumerate(hdrs, start=1):
            cell = ws2.cell(2, col_i, h)
            cell.font      = FONT_BOLD
            cell.fill      = FILL_YELLOW_HDR
            cell.alignment = ALIGN_C
            cell.border    = thin_border()

        row_cur = 3
        has_any = False
        for c_idx, conj in enumerate(todos_conjuntos):
            mpf_c = todos_mpf[c_idx] if c_idx < len(todos_mpf) else []
            vis_c = get_visual(c_idx)
            for i_f, f_nat in enumerate(conj):
                mpf   = mpf_c[i_f] if i_f < len(mpf_c) else {}
                xv    = mpf.get('x'); yv = mpf.get('y'); zv = mpf.get('z')
                if xv is None and yv is None and zv is None:
                    continue
                vals_ok = [v for v in (xv, yv, zv) if v is not None]
                if not any(v > MPF_LIMIAR for v in vals_ok):
                    continue
                for m in multiplicadores:
                    rpm_crit = (f_nat * 60) / m
                    # apenas cruzamentos DENTRO da zona de operação
                    if not (zona_min <= rpm_crit <= zona_max):
                        continue
                    valores  = [
                        vis_c['nome'],
                        f"M{i_f+1:02d}",
                        round(f_nat, 2),
                        f"{m}×",
                        round(rpm_crit, 1),
                        round(xv, 1) if xv is not None else "—",
                        round(yv, 1) if yv is not None else "—",
                        round(zv, 1) if zv is not None else "—",
                    ]
                    for col_i, val in enumerate(valores, start=1):
                        cell = ws2.cell(row_cur, col_i, val)
                        cell.alignment = ALIGN_C
                        cell.border    = thin_border()
                        # coloração por coluna
                        if col_i <= 5:
                            cell.fill = FILL_RED
                        elif col_i == 6:
                            cell.fill = FILL_RED if (xv is not None and xv > MPF_LIMIAR) else (FILL_GREEN if xv is not None else FILL_ORANGE)
                        elif col_i == 7:
                            cell.fill = FILL_RED if (yv is not None and yv > MPF_LIMIAR) else (FILL_GREEN if yv is not None else FILL_ORANGE)
                        elif col_i == 8:
                            cell.fill = FILL_RED if (zv is not None and zv > MPF_LIMIAR) else (FILL_GREEN if zv is not None else FILL_ORANGE)
                    row_cur += 1
                    has_any  = True

        if not has_any:
            ws2["A3"].value = "Nenhum ponto crítico encontrado."
            ws2["A3"].font  = Font(italic=True)

        # larguras
        for col_i, w in enumerate([18,8,10,10,12,10,8,8,8], start=1):
            ws2.column_dimensions[get_column_letter(col_i)].width = w
        ws2.row_dimensions[1].height = 18

    try:
        wb.save(str(caminho))
        return f"✔ Relatório salvo: {caminho}", closed_style
    except Exception as e:
        return f"✖ Erro Excel: {e}  (pip install openpyxl)", closed_style


# ── Clientside: restaura dimensões ao redimensionar janela ───────────────────
app.clientside_callback(
    """
    function() {
        if (!window._resizeListenerAdded) {
            window._resizeListenerAdded = true;
            window._lastW = window.innerWidth; window._lastH = window.innerHeight;
            function onResize() {
                var wW=window.innerWidth; var wH=window.innerHeight;
                if (wW===window._lastW && wH===window._lastH) return;
                window._lastW=wW; window._lastH=wH;
                var wInput=document.getElementById('x-max');
                var hInput=document.getElementById('y-max');
                if (!wInput || !hInput) return;
                var ev=new Event('change',{bubbles:true});
                wInput.dispatchEvent(ev); hInput.dispatchEvent(ev);
            }
            setInterval(onResize, 400);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('resonancia-graph', 'id'),
    Input('resonancia-graph',  'id'),
)


# ── Clientside: fechar dropdowns ao clicar fora ──────────────────────────────
app.clientside_callback(
    """
    function(id) {
        if (!window._dropdownOutsideListenerAdded) {
            window._dropdownOutsideListenerAdded = true;
            document.addEventListener('click', function(e) {
                var ids = ['pontos-dropdown-btn', 'pontos-dropdown-panel',
                           'modos-dropdown-btn',  'modos-dropdown-panel',
                           'excel-dropdown-btn',   'excel-dropdown-panel'];
                var inside = false;
                for (var i = 0; i < ids.length; i++) {
                    var el = document.getElementById(ids[i]);
                    if (el && el.contains(e.target)) { inside = true; break; }
                }
                if (!inside) {
                    var btn = document.getElementById('close-all-dropdowns');
                    if (btn) btn.click();
                }
            });
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('close-all-dropdowns', 'id'),
    Input('close-all-dropdowns',  'id'),
)

