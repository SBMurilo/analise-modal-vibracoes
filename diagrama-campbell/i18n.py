# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: i18n
# -----------------------------------------------------------------------------
# Dicionário _LANG_GRAPH com TODOS os textos que aparecem NO GRÁFICO em três
# idiomas — 'pt' (português), 'en' (inglês) e 'es' (espanhol):
#   • Títulos de eixo (X: RPM, Y: Hz) e rótulo da Zona de Operação
#   • Templates de hover: harmônicas, modos, cruzamentos (crítico e não),
#     linha de MPF X/Y/Z para o hover do ponto de cruzamento
#   • Legendas dos cruzamentos (na zona ativos/suprimidos, externos, MPF)
#   • Palavra base do conjunto ("Conjunto"/"Set") e o prefixo curto
#     ('C'/'S') usado nas legendas curtas C1, C2, S1... (Rev05.1)
# É consumido por figure.py (que formata os placeholders com os dados da
# sessão) e re-aplicado pelo callback `selecionar_idioma` em
# callbacks_diagram.py quando o usuário troca de bandeira.
# Não trata os textos da TELA INICIAL — esses são fixos em português no
# layout (rótulos dos inputs, botões etc).
# =============================================================================

_LANG_GRAPH = {
    'pt': dict(
        xaxis_title    = "Velocidade de Rotação (RPM)",
        yaxis_title    = "Frequência (Hz)",
        zona_label     = "<b>Zona de Operação</b>",
        speed_suffix   = "Velocidade",
        hover_harm     = "{m}× — {{x:.0f}} rpm → {{y:.2f}} Hz",
        hover_mode     = "M{n:02d} ({nome}) — {f} Hz",
        hover_label    = "<b>M{n:02d}</b> ({nome}) — clicar",
        crit_title     = "<b>⚠ Velocidade Crítica</b>",
        crit_harm      = "Harmônica   : {m}×",
        crit_rpm       = "RPM crítico : {rpm:.1f} rpm",
        crit_freq      = "Frequência  : {f:.1f} Hz (M{n:02d} — {nome})",
        cross_title    = "<b>Cruzamento</b>",
        cross_harm     = "Harmônica: {m}×",
        cross_rpm      = "RPM: {rpm:.1f} rpm",
        cross_freq     = "Frequência: {f:.1f} Hz (M{n:02d} — {nome})",
        mpf_line       = "MPF   X: {x}  Y: {y}  Z: {z}",
        conjunto_word  = "Conjunto",
        set_short_prefix = "C",
        leg_zona_on    = "{nome} Cruzamento - Modo Ativo",
        leg_zona_off   = "{nome} Cruzamento - Modo Suprimido",
        leg_ext_on     = "Fora da zona - Ativo",
        leg_ext_off    = "Fora da zona - Suprimido",
        leg_mpf        = "Cruzamentos Críticos - MPF > {limiar}%",
    ),
    'en': dict(
        xaxis_title    = "Rotation Speed (RPM)",
        yaxis_title    = "Frequency (Hz)",
        zona_label     = "<b>Operating Zone</b>",
        speed_suffix   = "Speed",
        hover_harm     = "{m}× — {{x:.0f}} rpm → {{y:.2f}} Hz",
        hover_mode     = "M{n:02d} ({nome}) — {f} Hz",
        hover_label    = "<b>M{n:02d}</b> ({nome}) — click",
        crit_title     = "<b>⚠ Critical Speed</b>",
        crit_harm      = "Harmonic    : {m}×",
        crit_rpm       = "Critical RPM: {rpm:.1f} rpm",
        crit_freq      = "Frequency   : {f:.1f} Hz (M{n:02d} — {nome})",
        cross_title    = "<b>Crossing</b>",
        cross_harm     = "Harmonic: {m}×",
        cross_rpm      = "RPM: {rpm:.1f} rpm",
        cross_freq     = "Frequency: {f:.1f} Hz (M{n:02d} — {nome})",
        mpf_line       = "MPF   X: {x}  Y: {y}  Z: {z}",
        conjunto_word  = "Set",
        set_short_prefix = "S",
        leg_zona_on    = "{nome} Crossing - Active Mode",
        leg_zona_off   = "{nome} Crossing - Suppressed Mode",
        leg_ext_on     = "Outside zone - Active",
        leg_ext_off    = "Outside zone - Suppressed",
        leg_mpf        = "Critical Crossings - MPF > {limiar}%",
    ),
    'es': dict(
        xaxis_title    = "Velocidad de Rotación (RPM)",
        yaxis_title    = "Frecuencia (Hz)",
        zona_label     = "<b>Zona de Operación</b>",
        speed_suffix   = "Velocidad",
        hover_harm     = "{m}× — {{x:.0f}} rpm → {{y:.2f}} Hz",
        hover_mode     = "M{n:02d} ({nome}) — {f} Hz",
        hover_label    = "<b>M{n:02d}</b> ({nome}) — clic",
        crit_title     = "<b>⚠ Velocidad Crítica</b>",
        crit_harm      = "Armónica    : {m}×",
        crit_rpm       = "RPM crítico : {rpm:.1f} rpm",
        crit_freq      = "Frecuencia  : {f:.1f} Hz (M{n:02d} — {nome})",
        cross_title    = "<b>Cruce</b>",
        cross_harm     = "Armónica: {m}×",
        cross_rpm      = "RPM: {rpm:.1f} rpm",
        cross_freq     = "Frecuencia: {f:.1f} Hz (M{n:02d} — {nome})",
        mpf_line       = "MPF   X: {x}  Y: {y}  Z: {z}",
        conjunto_word  = "Conjunto",
        set_short_prefix = "C",
        leg_zona_on    = "{nome} Cruce - Modo Activo",
        leg_zona_off   = "{nome} Cruce - Modo Suprimido",
        leg_ext_on     = "Fuera de zona - Activo",
        leg_ext_off    = "Fuera de zona - Suprimido",
        leg_mpf        = "Cruces Críticos - MPF > {limiar}%",
    ),
}
