# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: figure
# -----------------------------------------------------------------------------
# Motor gráfico do diagrama de Campbell — todas as funções que produzem ou
# modificam a figura Plotly vivem aqui:
#   gerar_figura(x_min, x_max, y_min, y_max, ...) — constrói a figura completa:
#                linhas de harmônica (1×, 2×, ..., um trace por múltiplo),
#                linhas horizontais dos modos por conjunto, pontos de
#                cruzamento (dentro e fora da zona), plaquinhas com o RPM
#                crítico de cada cruzamento, faixa cinza da zona de operação,
#                linhas verticais de Nmin/Nmax, e a legenda-chave dinâmica.
#                Retorna (fig, ann_map), onde ann_map é o dicionário que
#                mapeia grupos de harmônica → índices das plaquinhas.
#   _apply_all_states(fig, ann_map, hidden_modes, labels_on, dots_on)
#              — reaplica visibilidade de modos, pontos e plaquinhas sobre
#                uma figura existente (mais rápido que reconstruir do zero).
#                Respeita dots_on["mpf_vivid"] (Rev05.1: borda azul dos
#                cruzamentos críticos preservada em todas as cascatas).
#   _recalc_mode_labels — reposiciona as plaquinhas "M01, M02, ..." ao lado
#                do último modo visível sempre que o eixo X ou Y muda.
#   _is_mpf_critico_na_zona(c, i_f) — True se o modo (c, i_f) tem MPF acima
#                do limiar E ao menos uma harmônica cruza dentro da zona.
#   _apply_legend_key — decide a visibilidade de cada linha da legenda-chave
#                (Conjunto N ativo/suprimido, Externos, MPF) com base no
#                conteúdo real do gráfico.
#   _place_labels — solver interno de colisão entre plaquinhas RPM (com
#                rejeição por bounding-box para acelerar modelos densos).
# -----------------------------------------------------------------------------
# OTIMIZAÇÃO (Rev05): (a) construção da figura por dicts com um único
# go.Figure no fim (uma validação em vez de centenas); (b) rejeição por
# bounding-box no solucionador de rótulos de cruzamento. Ambas provadas
# byte-idênticas ao Rev04 — a figura gerada é exatamente a mesma.
# =============================================================================

import numpy as np
import plotly.graph_objects as go

from config  import NOME_BASE, FIG_HEIGHT
from i18n    import _LANG_GRAPH
from session import _g
from styles  import estilos_harm, get_visual

def _place_labels(init_sy: list, min_gap: float) -> list:
    """
    Distribui posições de labels verticalmente (pixels, eixo para baixo).
    Ao invés de ancorar o primeiro label e empurrar todos para baixo,
    resolve colisões espalhando cada par em torno do seu ponto médio.
    Isso mantém o grupo centralizado na posição natural média, aproveitando
    o espaço acima quando os modos estão concentrados na parte inferior.
    """
    n = len(init_sy)
    if n == 0:
        return []
    pos = list(init_sy)
    for _ in range(500):
        moved = False
        for j in range(1, n):
            if pos[j] < pos[j - 1] + min_gap:
                mid        = (pos[j - 1] + pos[j]) / 2.0
                pos[j - 1] = mid - min_gap / 2.0
                pos[j]     = mid + min_gap / 2.0
                moved = True
        if not moved:
            break
    return pos

def gerar_figura(x_min, x_max, y_min, y_max, fig_height=FIG_HEIGHT, lang='pt'):
    import math

    L = _LANG_GRAPH.get(lang, _LANG_GRAPH['pt'])

    todos_conjuntos = _g('todos_conjuntos', [])
    todos_mpf       = _g('todos_mpf', [])
    multiplicadores = _g('multiplicadores', [])
    n_min           = _g('n_min', 0)
    n_max           = _g('n_max', 1000)
    zona_min        = _g('zona_min', 0)
    zona_max        = _g('zona_max', 1000)
    rpm_max         = _g('rpm_max', 1000)
    titulo_usuario  = _g('titulo_usuario', '')

    def _mpf_hover_line(c, i_f):
        """Retorna linha de MPF para o hover, ou '' se dados ausentes."""
        if not todos_mpf or c >= len(todos_mpf) or i_f >= len(todos_mpf[c]):
            return ''
        mpf = todos_mpf[c][i_f]
        xv, yv, zv = mpf.get('x'), mpf.get('y'), mpf.get('z')
        if xv is None and yv is None and zv is None:
            return ''
        fmt = lambda v: f"{v:.1f}%" if v is not None else '—'
        return L['mpf_line'].format(x=fmt(xv), y=fmt(yv), z=fmt(zv)) + "<br>"

    if not todos_conjuntos:
        return go.Figure(), {}

    # ── Acumuladores: traços e anotações são montados como dicts e o
    #    go.Figure é criado UMA vez no fim (uma validação em vez de
    #    centenas de add_trace/add_annotation). Figura idêntica, bem mais rápida.
    _data   = []
    _ann    = []
    ann_map = {}
    def _addann(**kw):
        _ann.append(kw)

    line_end   = max(x_max, rpm_max)
    line_range = np.linspace(0, line_end, 500)

    # ── Rótulos por conjunto (Rev05.1) ────────────────────────────────────────
    # • short_prefix: derivado de i18n (fallback: 1ª letra de conjunto_word).
    # • short_names[c]  → "C1", "C2", ...  (usado nas legendas dos cruzamentos)
    # • nome_hover      → "Conjunto 1"     (mantido nos hovers como antes)
    # • nome_legenda    → "Conjunto 1 (C1)" (usado APENAS no name das linhas)
    short_prefix = L.get('set_short_prefix') or (L['conjunto_word'][:1] if L.get('conjunto_word') else 'C')
    short_names  = {c: f"{short_prefix}{c + 1}" for c in range(len(todos_conjuntos))}

    for c, conj in enumerate(todos_conjuntos):
        vis_c        = get_visual(c)
        nome_hover   = f"{L['conjunto_word']} {c + 1}"
        nome_legenda = f"{nome_hover} ({short_names[c]})"
        _data.append(dict(type='scatter',
            x=[None], y=[None], mode='lines',
            name=nome_legenda, legendgroup=f'modos_{c}',
            line=dict(color=vis_c['cor_linha'], width=vis_c['width_linha'],
                      dash=vis_c['dash_linha']),
            showlegend=True,
        ))
        for i, f in enumerate(conj):
            _data.append(dict(type='scatter',
                x=[0, line_end], y=[f, f], mode='lines',
                name=nome_legenda, legendgroup=f'modos_{c}',
                customdata=[f"modo_{c}_{i}", f"modo_{c}_{i}"],
                line=dict(color=vis_c['cor_linha'], width=vis_c['width_linha'],
                          dash=vis_c['dash_linha']),
                showlegend=False,
                hovertemplate=L['hover_mode'].format(n=i+1, nome=nome_hover, f=f) + "<extra></extra>",
            ))

    # Nomes traduzidos por índice de conjunto (usados nos hovers das labels e cruzamentos)
    nomes_trad = {c: f"{L['conjunto_word']} {c + 1}" for c in range(len(todos_conjuntos))}

    plot_area_px = max(fig_height - 180, 100)
    y_range      = max(y_max - y_min, 1.0)
    px_per_hz    = plot_area_px / y_range
    MIN_GAP_PX   = 22

    all_vis_modes = []
    for c, conj in enumerate(todos_conjuntos):
        for i, f in enumerate(conj):
            if y_min <= f <= y_max:
                all_vis_modes.append((f, c, i))

    all_vis_sorted = sorted(all_vis_modes, key=lambda t: -t[0])
    init_sy = [(y_max - f) * px_per_hz - 10 for f, _, _ in all_vis_sorted]
    text_sy = _place_labels(init_sy, MIN_GAP_PX)

    plot_w_px  = max(fig_height * 1.8 - 120, 200)
    hz_per_px  = y_range / plot_area_px
    rpm_per_px = max(x_max - x_min, 1.0) / plot_w_px

    for j, (f, c, i) in enumerate(all_vis_sorted):
        vis_c     = get_visual(c)
        anchor_sy = (y_max - f) * px_per_hz
        ay_adj    = text_sy[j] - anchor_sy
        ann_idx   = len(_ann)
        _addann(
            xref='x', yref='y', x=x_max, y=f,
            ax=24, ay=ay_adj, axref='pixel', ayref='pixel',
            text=f"<b>M{i+1:02d}</b>", showarrow=True,
            arrowhead=2, arrowsize=0.7, arrowwidth=1.1,
            arrowcolor=vis_c['cor_borda_plaq'],
            xanchor='left', yanchor='bottom',
            font=dict(size=10, color=vis_c['cor_texto_plaq']),
            bgcolor=vis_c['cor_bg_plaq'],
            bordercolor=vis_c['cor_borda_plaq'], borderwidth=0.6, borderpad=3,
        )
        ann_map.setdefault(f"modo_{c}_{i}", []).append(ann_idx)
        lbl_cx = x_max + (24 + 32) * rpm_per_px
        lbl_cy = f - ay_adj * hz_per_px + 9 * hz_per_px
        _data.append(dict(type='scatter',
            x=[lbl_cx], y=[lbl_cy], mode='markers',
            marker=dict(size=22, color='rgba(0,0,0,0)', opacity=0, line=dict(width=0)),
            customdata=[f"label_modo_{c}_{i}"],
            showlegend=False,
            hovertemplate=L['hover_label'].format(n=i+1, nome=nomes_trad[c]) + "<extra></extra>",
            cliponaxis=False,
        ))

    for i, m in enumerate(multiplicadores):
        y_vals = m * (line_range / 60)
        est    = estilos_harm[i % len(estilos_harm)]
        grupo  = f"harm_{m}"
        _data.append(dict(type='scatter',
            x=line_range, y=y_vals, mode='lines',
            name=f"{m}x {L['speed_suffix']}", legendgroup=grupo,
            line=dict(color=est['color'], width=est['width'], dash=est['dash']),
            opacity=0.9, showlegend=True,
            hovertemplate=L['hover_harm'].format(m=m) + "<extra></extra>",
        ))
        y_at_xmax = m * (x_max / 60)
        if y_at_xmax >= y_min:
            if y_at_xmax > y_max:
                x_label, y_label = (y_max * 60) / m, y_max
                xanchor_, yanchor_ = 'right', 'top'
            else:
                x_label, y_label = x_max, y_at_xmax
                xanchor_, yanchor_ = 'right', 'middle'
            if x_label >= x_min:
                _addann(
                    xref='x', yref='y', x=x_label, y=y_label,
                    text=f"<b>{m}X</b>", showarrow=False,
                    xanchor=xanchor_, yanchor=yanchor_,
                    font=dict(size=11, color=est['color']),
                    bgcolor='rgba(255,255,255,0.85)',
                    bordercolor=est['color'], borderwidth=0.8, borderpad=2,
                )

    LBL_W = 62;  LBL_H = 17;  DOT_R = 10;  GAP = 4
    plot_w_px  = max(fig_height * 1.8 - 120, 200)
    plot_h_px  = max(fig_height - 180, 100)
    px_per_rpm = plot_w_px / max(x_max - x_min, 1.0)
    px_per_hz2 = plot_h_px / max(y_max - y_min, 1.0)

    def gen_candidates():
        pref  = [315,300,330,285,345,270,260,280,0,20,340,45,30,60,15,90,75,105,225,240,210,250,180,200,160,135,120,150]
        seen  = set()
        angles = [a for a in pref if not (a in seen or seen.add(a))]
        cands = []
        for r in range(20, 125, 4):
            for ang in angles:
                rad = math.radians(ang)
                cands.append((r * math.cos(rad), r * math.sin(rad)))
        return cands

    CANDS = gen_candidates()

    def in_bounds(cx, cy):
        return (cx - LBL_W/2 >= GAP and cx + LBL_W/2 <= plot_w_px - GAP and
                cy - LBL_H/2 >= GAP and cy + LBL_H/2 <= plot_h_px - GAP)

    def rect_overlap(ax, ay, bx, by):
        return (abs(ax-bx) < LBL_W+GAP and abs(ay-by) < LBL_H+GAP)

    def dot_in_label(cx, cy, px, py):
        lx0 = cx-LBL_W/2-GAP; lx1 = cx+LBL_W/2+GAP
        ly0 = cy-LBL_H/2-GAP; ly1 = cy+LBL_H/2+GAP
        # Rejeição rápida por caixa (resultado idêntico): se o ponto está a mais
        # de DOT_R de distância da caixa do rótulo em qualquer eixo, não há como
        # a distância ao retângulo ser < DOT_R.
        if px < lx0-DOT_R or px > lx1+DOT_R or py < ly0-DOT_R or py > ly1+DOT_R:
            return False
        nx = max(lx0, min(px, lx1)); ny = max(ly0, min(py, ly1))
        return (nx-px)**2 + (ny-py)**2 < DOT_R**2

    def segments_cross(x1,y1,x2,y2,x3,y3,x4,y4):
        # Rejeição rápida por caixa envolvente (resultado idêntico): se as caixas
        # dos dois segmentos não se sobrepõem, eles não podem se cruzar.
        if (x1 < x3 and x2 < x3 and x1 < x4 and x2 < x4) or \
           (x1 > x3 and x2 > x3 and x1 > x4 and x2 > x4) or \
           (y1 < y3 and y2 < y3 and y1 < y4 and y2 < y4) or \
           (y1 > y3 and y2 > y3 and y1 > y4 and y2 > y4):
            return False
        rx,ry = x2-x1, y2-y1; sx,sy = x4-x3, y4-y3
        denom = rx*sy - ry*sx                       # _cross2d(rx,ry,sx,sy) inline
        if abs(denom) < 1e-10: return False
        qpx,qpy = x3-x1, y3-y1
        t = (qpx*sy - qpy*sx)/denom                 # _cross2d(qp, s) inline
        u = (qpx*ry - qpy*rx)/denom                 # _cross2d(qp, r) inline
        return 0.05 < t < 0.95 and 0.05 < u < 0.95

    def arrow_hits_label_rect(ax1,ay1,ax2,ay2,cx,cy):
        hw,hh = LBL_W/2+GAP, LBL_H/2+GAP
        lx0,lx1 = cx-hw, cx+hw; ly0,ly1 = cy-hh, cy+hh
        # Rejeição rápida por caixa (resultado idêntico): se a caixa da seta não
        # toca a caixa do rótulo, ela não cruza nenhuma das 4 arestas.
        if (ax1 < lx0 and ax2 < lx0) or (ax1 > lx1 and ax2 > lx1) or \
           (ay1 < ly0 and ay2 < ly0) or (ay1 > ly1 and ay2 > ly1):
            return False
        for ex1,ey1,ex2,ey2 in [(lx0,ly0,lx1,ly0),(lx1,ly0,lx1,ly1),(lx1,ly1,lx0,ly1),(lx0,ly1,lx0,ly0)]:
            if segments_cross(ax1,ay1,ax2,ay2,ex1,ey1,ex2,ey2): return True
        return False

    callout_pts = []
    for m in multiplicadores:
        grupo = f"harm_{m}"
        for c, conj in enumerate(todos_conjuntos):
            vis_c = get_visual(c)
            for i_f, f in enumerate(conj):
                rpm_crit = (f * 60) / m
                if rpm_crit > line_end or not (zona_min <= rpm_crit <= zona_max):
                    continue
                _data.append(dict(type='scatter',
                    x=[rpm_crit], y=[f], mode='markers',
                    marker=dict(color=vis_c['cor_ponto_zona'], size=11, symbol='circle',
                                line=dict(width=2.0, color=vis_c['cor_ponto_zona_linha'])),
                    customdata=[f"cruzamento_harm_{m}_conj_{c}_modo_{i_f}"],
                    showlegend=False,
                    hovertemplate=(L['crit_title'] + "<br>"
                                   + L['crit_harm'].format(m=m) + "<br>"
                                   + L['crit_rpm'].format(rpm=rpm_crit) + "<br>"
                                   + L['crit_freq'].format(f=f, n=i_f+1, nome=nomes_trad[c]) + "<br>"
                                   + _mpf_hover_line(c, i_f)
                                   + "<extra></extra>"),
                ))
                callout_pts.append((rpm_crit, f, grupo, c, i_f))

    callout_pts.sort(key=lambda t: (-t[1], -t[0]))
    anchors       = [((r - x_min)*px_per_rpm, (y_max - fq)*px_per_hz2) for r, fq, _, _, _ in callout_pts]
    placed        = []
    placed_arrows = []

    for idx, (rpm_crit, f, grupo, c_pt, i_f) in enumerate(callout_pts):
        ax_px, ay_px = anchors[idx]
        chosen = None
        for cax, cay in CANDS:
            cx, cy = ax_px+cax, ay_px+cay
            if not in_bounds(cx, cy): continue
            if any(rect_overlap(cx,cy,ox,oy) for ox,oy in placed): continue
            if any(dot_in_label(cx,cy,px,py) for j,(px,py) in enumerate(anchors) if j!=idx): continue
            if any(arrow_hits_label_rect(ax_px,ay_px,cx,cy,ox,oy) for ox,oy in placed): continue
            if any(segments_cross(ax_px,ay_px,cx,cy,bx1,by1,bx2,by2) for bx1,by1,bx2,by2 in placed_arrows): continue
            chosen = (cax, cay); placed.append((cx,cy)); placed_arrows.append((ax_px,ay_px,cx,cy)); break
        else:
            best_score = float('inf'); best_cand = None
            for cax, cay in CANDS:
                cx2,cy2 = ax_px+cax, ay_px+cay
                if not in_bounds(cx2, cy2): continue
                score  = sum(3 for ox,oy in placed if rect_overlap(cx2,cy2,ox,oy))
                score += sum(5 for j,(px,py) in enumerate(anchors) if j!=idx and dot_in_label(cx2,cy2,px,py))
                score += sum(1 for ox,oy in placed if arrow_hits_label_rect(ax_px,ay_px,cx2,cy2,ox,oy))
                score += sum(1 for bx1,by1,bx2,by2 in placed_arrows if segments_cross(ax_px,ay_px,cx2,cy2,bx1,by1,bx2,by2))
                if score < best_score: best_score=score; best_cand=(cax,cay)
            chosen = best_cand if best_cand is not None else CANDS[0]
            cx, cy = ax_px+chosen[0], ay_px+chosen[1]
            placed.append((cx,cy)); placed_arrows.append((ax_px,ay_px,cx,cy))

        ann_idx = len(_ann)
        _addann(
            x=rpm_crit, y=f, xref='x', yref='y',
            ax=chosen[0], ay=chosen[1], axref='pixel', ayref='pixel',
            text=f"<b>{rpm_crit:.0f} rpm</b>", showarrow=True,
            arrowhead=0, arrowwidth=2, arrowcolor='rgba(160,0,20,0.5)',
            bgcolor='rgba(255,220,220,0.55)', bordercolor='rgba(180,0,0,0.45)',
            borderwidth=1.0, borderpad=4,
            font=dict(size=9, color='rgba(140,0,0,0.85)', family='Arial'),
            visible=True,
        )
        ann_map.setdefault(grupo, []).append([ann_idx, c_pt, i_f])

    for m in multiplicadores:
        for c, conj in enumerate(todos_conjuntos):
            vis_c = get_visual(c)
            for i_f, f in enumerate(conj):
                rpm_crit = (f * 60) / m
                if rpm_crit > line_end or zona_min <= rpm_crit <= zona_max:
                    continue
                _data.append(dict(type='scatter',
                    x=[rpm_crit], y=[f], mode='markers',
                    marker=dict(color='limegreen', size=9, symbol='circle',
                                line=dict(width=2, color='black')),
                    customdata=[f"ext_harm_{m}_conj_{c}_modo_{i_f}"],
                    showlegend=False,
                    hovertemplate=(L['cross_title'] + "<br>"
                                   + L['cross_harm'].format(m=m) + "<br>"
                                   + L['cross_rpm'].format(rpm=rpm_crit) + "<br>"
                                   + L['cross_freq'].format(f=f, n=i_f+1, nome=nomes_trad[c]) + "<br>"
                                   + _mpf_hover_line(c, i_f)
                                   + "<extra></extra>"),
                ))

    # ── Entradas de LEGENDA-CHAVE dos pontos de cruzamento ────────────────────
    # São traços "fantasma" (x/y = None) usados apenas para exibir a legenda.
    # A visibilidade real de cada entrada é definida por _apply_legend_key(),
    # de acordo com os toggles de Pontos/Externos/Pontos MPF e o estado de
    # visibilidade (considerado = aceso / não considerado = apagado) dos modos.
    # Convenção 'considerado/não considerado':
    #   aceso  = modo ATIVO  (participa da análise)  → ponto claro
    #   apagado= modo OCULTO (excluído da análise)   → ponto apagado
    for c in range(len(todos_conjuntos)):
        vis_c = get_visual(c)
        # Rev05.1: legendas dos cruzamentos usam o rótulo CURTO ("C1", "C2"...)
        # ao invés do nome longo ("Conjunto 1"), para caber melhor na legenda.
        nome  = short_names[c]
        # Na zona — considerado (aceso), na cor do conjunto
        _data.append(dict(type='scatter',
            x=[None], y=[None], mode='markers',
            name=L['leg_zona_on'].format(nome=nome),
            marker=dict(size=11, symbol='circle',
                        color=vis_c['cor_ponto_zona'],
                        line=dict(width=2.0, color=vis_c['cor_ponto_zona_linha'])),
            customdata=[f"legendkey_zona_{c}_on"],
            legendgroup=f"legendkey_zona_{c}",
            showlegend=True, visible=False, hoverinfo='skip',
        ))
        # Na zona — não considerado (apagado), mesma cor com opacidade reduzida
        _data.append(dict(type='scatter',
            x=[None], y=[None], mode='markers',
            name=L['leg_zona_off'].format(nome=nome),
            marker=dict(size=11, symbol='circle',
                        color=vis_c['cor_ponto_zona'],
                        line=dict(width=2.0, color=vis_c['cor_ponto_zona_linha'])),
            opacity=0.30,
            customdata=[f"legendkey_zona_{c}_off"],
            legendgroup=f"legendkey_zona_{c}",
            showlegend=True, visible=False, hoverinfo='skip',
        ))

    # Externos (verde) — compartilhado por todos os conjuntos
    _data.append(dict(type='scatter',
        x=[None], y=[None], mode='markers',
        name=L['leg_ext_on'],
        marker=dict(size=9, symbol='circle', color='limegreen',
                    line=dict(width=2, color='black')),
        customdata=["legendkey_ext_on"],
        legendgroup="legendkey_ext",
        showlegend=True, visible=False, hoverinfo='skip',
    ))
    _data.append(dict(type='scatter',
        x=[None], y=[None], mode='markers',
        name=L['leg_ext_off'],
        marker=dict(size=9, symbol='circle', color='limegreen',
                    line=dict(width=2, color='black')),
        opacity=0.30,
        customdata=["legendkey_ext_off"],
        legendgroup="legendkey_ext",
        showlegend=True, visible=False, hoverinfo='skip',
    ))

    # Pontos MPF (destaque: maior + borda azul)
    # Rev05.1: o rótulo agora contém o limiar informado na tela inicial
    # (ex.: "Cruzamentos Críticos - MPF > 5%"). Formata como inteiro quando
    # possível, senão como decimal enxuto ('%g' remove zeros à direita).
    _mpf_limiar = _g('mpf_limiar', 5.0)
    _limiar_str = (f"{int(_mpf_limiar)}" if float(_mpf_limiar) == int(_mpf_limiar)
                   else f"{float(_mpf_limiar):g}")
    _data.append(dict(type='scatter',
        x=[None], y=[None], mode='markers',
        name=L['leg_mpf'].format(limiar=_limiar_str),
        marker=dict(size=15, symbol='circle', color='rgba(210,210,210,0.9)',
                    line=dict(width=2.6, color='#1565c0')),
        customdata=["legendkey_mpf"],
        legendgroup="legendkey_mpf",
        showlegend=True, visible=False, hoverinfo='skip',
    ))

    zona_center = (zona_min + zona_max) / 2
    _addann(
        xref='x', yref='paper', x=zona_center, y=1.035,
        text=L['zona_label'], showarrow=False,
        xanchor='center', yanchor='bottom',
        font=dict(size=12, color='#333333', family='Arial'),
        bgcolor='rgba(220,220,220,0.85)', bordercolor='#555', borderwidth=1.0, borderpad=4,
    )
    vistos_vline = set()
    _vlines = []
    for x_val, label_text in [(n_min, f"<b>{n_min:.0f} rpm</b>"),
                               (n_max, f"<b>{n_max:.0f} rpm</b>")]:
        if x_val in vistos_vline: continue
        vistos_vline.add(x_val)
        _vlines.append(x_val)
        _addann(
            xref='x', yref='paper', x=x_val, y=1,
            text=label_text, showarrow=False,
            xanchor='center', yanchor='bottom',
            font=dict(size=11, color='black'),
        )

    effective_y_min = y_min
    # ── Construção ÚNICA da figura (uma validação para todos os traços/anotações)
    fig = go.Figure(data=_data)
    fig.update_layout(
        annotations=_ann,
        title=dict(text=f"{NOME_BASE}<br><sup>{titulo_usuario}</sup>"),
        xaxis_title=L['xaxis_title'],
        yaxis_title=L['yaxis_title'],
        xaxis=dict(gridcolor='lightgray', showgrid=True,
                   zeroline=(x_min == 0), zerolinecolor='lightgray', zerolinewidth=1,
                   range=[x_min, x_max],
                   showline=True, linecolor='black', linewidth=1.5, mirror=True,
                   dtick=50, tick0=0, ticks='outside', ticklen=6, tickwidth=1.5, tickcolor='black',
                   automargin=True),
        yaxis=dict(gridcolor='lightgray', showgrid=True,
                   zeroline=(y_min == 0), zerolinecolor='lightgray', zerolinewidth=1,
                   range=[effective_y_min, y_max],
                   showline=True, linecolor='black', linewidth=1.5, mirror=True,
                   ticks='outside', ticklen=6, tickwidth=1.5, tickcolor='black',
                   automargin=True),
        plot_bgcolor='white',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
        ),
        height=FIG_HEIGHT,
        margin=dict(r=90, t=60, b=80),
    )
    # Formas (poucas e baratas — mantidas nos métodos testados do Plotly):
    fig.add_vrect(x0=zona_min, x1=zona_max,
                  fillcolor="gray", opacity=0.3, layer="below", line_width=0)
    for x_val in _vlines:
        fig.add_vline(x=x_val, line=dict(color="black", width=2.0, dash="dot"))
    return fig, ann_map


# =============================================================================
# 7. HELPERS DE VISIBILIDADE  
# =============================================================================

def _apply_all_states(fig, ann_map, hidden_modes, labels_on, dots_on):
    todos_conjuntos = _g('todos_conjuntos', [])
    multiplicadores = _g('multiplicadores', [])
    N_CONJ          = _g('N_CONJ', 0)

    if hidden_modes is None:
        hidden_modes = {"0": []}
    if dots_on is None:
        dots_on = {str(c): (c == 0) for c in range(N_CONJ)}

    visible_sets = {}
    for c in range(N_CONJ):
        all_idx = set(range(len(todos_conjuntos[c])))
        hidden  = set(hidden_modes.get(str(c), []))
        visible_sets[c] = all_idx - hidden

    for t in fig.data:
        if not hasattr(t, 'customdata') or t.customdata is None or len(t.customdata) == 0:
            continue
        cd = t.customdata[0]
        if not isinstance(cd, str): continue

        if cd.startswith('modo_'):
            parts = cd.split('_'); c_t, i_t = int(parts[1]), int(parts[2])
            t.visible = (i_t in visible_sets.get(c_t, set()))

        elif cd.startswith('label_modo_'):
            parts = cd.split('_'); c_t, i_t = int(parts[2]), int(parts[3])
            t.visible = (i_t in visible_sets.get(c_t, set()))

        elif cd.startswith('cruzamento_') and '_conj_' in cd:
            try:
                conj_part    = cd.rsplit('_conj_', 1)[1]
                c_str, i_str = conj_part.split('_modo_')
                c_t, i_t     = int(c_str), int(i_str)
            except (ValueError, IndexError): continue
            vis_c     = get_visual(c_t)
            is_active = (i_t in visible_sets.get(c_t, set()))
            dots_c_on = bool(dots_on.get(str(c_t), c_t == 0))
            if is_active:
                t.marker.color      = vis_c['cor_ponto_zona']
                t.marker.line.color = vis_c['cor_ponto_zona_linha']
                t.marker.line.width = 2.0
            else:
                t.marker.color      = vis_c['cor_ponto_zona_t']
                t.marker.line.color = vis_c['cor_ponto_zona_linha_t']
            # ── Rev05.1: preserva o destaque vívido MPF ──────────────────────
            # dots_on["mpf_vivid"] é a fonte da verdade para o botão "◆ Pontos
            # MPF". Sem este bloco, qualquer callback que chame _apply_all_states
            # (atualizar, toggle_modos_checklist, aplicar_criticos, selecionar_
            # idioma) após aplicar_criticos/toggle_mpf_vivid apagaria a borda
            # azul dos cruzamentos críticos ao sobrescrever line.color/width
            # com a cor padrão do conjunto. size=16 replica exatamente o que
            # toggle_mpf_vivid aplica quando o botão fica ligado.
            if is_active and bool(dots_on.get('mpf_vivid', False)) \
                         and _is_mpf_critico_na_zona(c_t, i_t):
                t.marker.size       = 16
                t.marker.line.color = '#1565c0'
                t.marker.line.width = 2.5
            else:
                t.marker.size       = 11
            t.visible = dots_c_on

        elif cd.startswith('ext_') and '_conj_' in cd:
            try:
                conj_part    = cd.rsplit('_conj_', 1)[1]
                c_str, i_str = conj_part.split('_modo_')
                c_t, i_t     = int(c_str), int(i_str)
            except (ValueError, IndexError): continue
            is_active = (i_t in visible_sets.get(c_t, set()))
            ext_on    = bool(dots_on.get("ext", True))
            zona_on   = bool(dots_on.get(str(c_t), c_t == 0))
            if is_active:
                t.marker.color      = 'limegreen'
                t.marker.line.color = 'black'
                t.marker.line.width = 2
            else:
                t.marker.color      = 'rgba(0,200,0,0.12)'
                t.marker.line.color = 'rgba(0,0,0,0.10)'
            t.visible = ext_on and zona_on

    if not ann_map: return
    annotations = list(fig.layout.annotations)
    for c in range(N_CONJ):
        for i in range(len(todos_conjuntos[c])):
            key = f"modo_{c}_{i}"
            if key in ann_map:
                is_active = (i in visible_sets.get(c, set()))
                for ai in ann_map[key]:
                    if ai < len(annotations):
                        annotations[ai].visible = is_active
    for m in multiplicadores:
        key = f"harm_{m}"
        if key not in ann_map: continue
        for entry in ann_map[key]:
            if isinstance(entry, (list, tuple)) and len(entry) >= 3:
                ann_idx, c_e, i_e = int(entry[0]), int(entry[1]), int(entry[2])
            else:
                ann_idx = int(entry); c_e = None; i_e = None
            if ann_idx >= len(annotations): continue
            is_active = (i_e in visible_sets.get(c_e, set())) if c_e is not None and i_e is not None else True
            dots_c_on = bool(dots_on.get(str(c_e), c_e == 0)) if c_e is not None else True
            annotations[ann_idx].visible = is_active and bool(labels_on) and dots_c_on
    fig.layout.annotations = annotations


def _recalc_mode_labels(fig, ann_map, visible_sets,
                        x_max, y_min, y_max, fig_height=FIG_HEIGHT, x_min=0):
    todos_conjuntos = _g('todos_conjuntos', [])
    if not ann_map: return

    plot_area_px = max(fig_height - 180, 100)
    y_range      = max(y_max - y_min, 1.0)
    px_per_hz    = plot_area_px / y_range
    MIN_GAP_PX   = 22

    all_vis_modes = []
    for c, conj in enumerate(todos_conjuntos):
        for i, f in enumerate(conj):
            key = f"modo_{c}_{i}"
            if key not in ann_map: continue
            if i not in visible_sets.get(c, set()): continue
            if y_min <= f <= y_max:
                all_vis_modes.append((f, c, i))

    all_vis_sorted = sorted(all_vis_modes, key=lambda t: -t[0])
    init_sy = [(y_max - f) * px_per_hz - 10 for f, _, _ in all_vis_sorted]
    text_sy = _place_labels(init_sy, MIN_GAP_PX)

    vis_keys    = {(c, i) for _, c, i in all_vis_sorted}
    annotations = list(fig.layout.annotations)

    for j, (f, c, i) in enumerate(all_vis_sorted):
        key = f"modo_{c}_{i}"
        if key not in ann_map: continue
        anchor_sy = (y_max - f) * px_per_hz
        ay_adj    = text_sy[j] - anchor_sy
        for ai in ann_map[key]:
            if ai < len(annotations):
                annotations[ai].ax      = 24
                annotations[ai].ay      = ay_adj
                annotations[ai].visible = True

    for c, conj in enumerate(todos_conjuntos):
        for i in range(len(conj)):
            key = f"modo_{c}_{i}"
            if key not in ann_map: continue
            if (c, i) not in vis_keys:
                for ai in ann_map[key]:
                    if ai < len(annotations):
                        annotations[ai].visible = False

    fig.layout.annotations = annotations


def _is_mpf_critico_na_zona(c, i_f):
    """
    True se o modo (c, i_f) possui MPF acima do limiar em algum eixo E ao
    menos uma harmônica cruza dentro da zona de operação.
    Lê tudo da sessão global (uso local, monousuário).
    """
    todos_mpf = _g('todos_mpf', [])
    if not todos_mpf or c >= len(todos_mpf) or i_f >= len(todos_mpf[c]):
        return False
    mpf  = todos_mpf[c][i_f]
    vals = [v for v in (mpf.get('x'), mpf.get('y'), mpf.get('z')) if v is not None]
    MPF_LIMIAR = _g('mpf_limiar', 5.0)
    if not vals or not any(v > MPF_LIMIAR for v in vals):
        return False
    todos_conjuntos = _g('todos_conjuntos', [])
    multiplicadores = _g('multiplicadores', [])
    zona_min = _g('zona_min', 0)
    zona_max = _g('zona_max', 0)
    if c < len(todos_conjuntos) and i_f < len(todos_conjuntos[c]):
        f = todos_conjuntos[c][i_f]
        return any(zona_min <= (f * 60) / m <= zona_max for m in multiplicadores)
    return False


def _apply_legend_key(fig, dots_on, hidden_modes):
    """
    Ajusta a visibilidade das entradas de LEGENDA-CHAVE (traços com customdata
    'legendkey_...') para refletir exatamente os pontos de cruzamento
    desenhados no gráfico no momento.

    Regras (espelham a lógica de desenho/visibilidade dos pontos reais):
      • 'legendkey_zona_{c}_on'  → há cruzamento NA ZONA de um modo ATIVO do
        conjunto c, com os pontos da zona do conjunto ligados.
      • 'legendkey_zona_{c}_off' → há cruzamento NA ZONA de um modo OCULTO do
        conjunto c, com os pontos da zona do conjunto ligados.
      • 'legendkey_ext_on/off'   → idem para pontos FORA da zona (verde),
        respeitando o toggle 'Externos' e o toggle da zona do conjunto.
      • 'legendkey_mpf'          → destaque de Pontos MPF ativo e existe ao
        menos um ponto MPF crítico na zona (modo ativo).
    """
    N_CONJ          = _g('N_CONJ', 0)
    todos_conjuntos = _g('todos_conjuntos', [])
    dots_on      = dots_on or {}
    hidden_modes = hidden_modes or {}
    ext_on = bool(dots_on.get('ext', True))
    mpf_on = bool(dots_on.get('mpf_vivid', False))

    visible_sets = {}
    for c in range(N_CONJ):
        all_idx = set(range(len(todos_conjuntos[c])))
        hidden  = set(hidden_modes.get(str(c), []))
        visible_sets[c] = all_idx - hidden

    zona_bright = {c: False for c in range(N_CONJ)}
    zona_dim    = {c: False for c in range(N_CONJ)}
    ext_bright  = False
    ext_dim     = False
    mpf_flag    = False

    # 1ª passada: descobre quais categorias possuem pontos desenhados
    for t in fig.data:
        if not hasattr(t, 'customdata') or not t.customdata or len(t.customdata) == 0:
            continue
        cd = t.customdata[0]
        if not isinstance(cd, str):
            continue
        if cd.startswith('cruzamento_') and '_conj_' in cd:
            try:
                tail = cd.rsplit('_conj_', 1)[1]
                c_t  = int(tail.split('_modo_')[0])
                i_t  = int(tail.split('_modo_')[1])
            except (ValueError, IndexError):
                continue
            if not bool(dots_on.get(str(c_t), c_t == 0)):
                continue
            active = (i_t in visible_sets.get(c_t, set()))
            if active:
                zona_bright[c_t] = True
                if mpf_on and _is_mpf_critico_na_zona(c_t, i_t):
                    mpf_flag = True
            else:
                zona_dim[c_t] = True
        elif cd.startswith('ext_') and '_conj_' in cd:
            try:
                tail = cd.rsplit('_conj_', 1)[1]
                c_t  = int(tail.split('_modo_')[0])
                i_t  = int(tail.split('_modo_')[1])
            except (ValueError, IndexError):
                continue
            if not (ext_on and bool(dots_on.get(str(c_t), c_t == 0))):
                continue
            active = (i_t in visible_sets.get(c_t, set()))
            if active:
                ext_bright = True
            else:
                ext_dim = True

    # 2ª passada: aplica a visibilidade calculada às entradas de legenda
    for t in fig.data:
        if not hasattr(t, 'customdata') or not t.customdata or len(t.customdata) == 0:
            continue
        cd = t.customdata[0]
        if not isinstance(cd, str) or not cd.startswith('legendkey_'):
            continue
        if cd.startswith('legendkey_zona_'):
            try:
                body        = cd[len('legendkey_zona_'):]
                c_str, kind = body.rsplit('_', 1)
                c_i         = int(c_str)
            except (ValueError, IndexError):
                t.visible = False
                continue
            t.visible = zona_bright.get(c_i, False) if kind == 'on' else zona_dim.get(c_i, False)
        elif cd == 'legendkey_ext_on':
            t.visible = ext_bright
        elif cd == 'legendkey_ext_off':
            t.visible = ext_dim
        elif cd == 'legendkey_mpf':
            t.visible = mpf_flag

