# =============================================================================
# Diagrama de Frequências Naturais X Excitações — Rev05
# Módulo: main
# -----------------------------------------------------------------------------
# Fio condutor da aplicação:
#   • Importa `app` (instância única do Dash, definida em app_instance.py).
#   • Importa `layout` e os três módulos de callbacks. A importação em si tem
#     efeito colateral: `layout.py` define `app.layout` e cada callbacks_*.py
#     registra seus callbacks no app via @callback / app.clientside_callback.
#     A ORDEM importa: layout precisa vir antes dos callbacks.
#   • Expõe `run()` — ponto de entrada: tenta abrir numa janela pywebview;
#     se o pywebview não estiver instalado, cai no navegador em
#     http://127.0.0.1:8050.
#   • Executado diretamente: `python main.py`.
# =============================================================================
#  HISTÓRICO DE REVISÕES
# -----------------------------------------------------------------------------
#  Rev.   | Data       | Autor            | Descrição da alteração
# -----------------------------------------------------------------------------
#  00     | 31/03/2026 | Murilo Battaglini|
#  01     | 23/04/2026 | Murilo Battaglini|
#  02     | 27/04/2026 | Murilo Battaglini|
#  03     | 13/05/2026 | Murilo Battaglini|
#  03.1   | 13/05/2026 | Murilo Battaglini| Adição de Controle de Revisão
#  04     | 12/08/2026 | Murilo Battaglini| Legenda-chave dinâmica dos pontos de cruzamento (na zona: considerado/aceso e não considerado/apagado por conjunto; externos verdes; destaque Pontos MPF).
#  05     | 12/08/2026 | Murilo Battaglini| Divisão do monólito em módulos com imports absolutos, executável direto (python main.py OU este launcher). OTIMIZAÇÃO DE DESEMPENHO em figure.py
#  05.1   | 14/08/2026 | Murilo Battaglini| Polimento da legenda-chave e acoplamento do botão "⚠ Críticos" com "◆ Pontos MPF"

# -----------------------------------------------------------------------------
#  Convenção de numeração:
#   - Revisão INTEIRA (ex: Rev01, Rev02, Rev03) — alteração estrutural ou
#     funcional relevante: mudança de cálculo, novo recurso, alteração de
#     layout/fluxo, correção que afeta resultado. Atualiza o nome do arquivo
#     launcher.
#   - Sub-revisão (ex: Rev03.1, Rev03.2, ...) — alteração pontual/menor que
#     NÃO altera o comportamento principal. Não renomeia o launcher.
#   - Ao fechar uma nova revisão inteira, a numeração decimal reinicia.
# =============================================================================

import threading
import time

from app_instance import app          # instância única do Dash
from config import NOME_BASE

# A importação destes módulos tem efeitos colaterais que REGISTRAM o layout e
# os callbacks no app. A ordem importa: layout antes dos callbacks.
import layout                    # noqa: F401  (define app.layout)
import callbacks_setup           # noqa: F401  (registra callbacks)
import callbacks_diagram         # noqa: F401  (registra callbacks + clientside)
import callbacks_export          # noqa: F401  (registra callbacks + clientside)


def _porta_disponivel(porta: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', porta)) != 0


def iniciar_dash():
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    app.run(debug=False, port=8050)


def run():
    """Ponto de entrada: abre em janela pywebview; se ausente, cai no navegador."""
    try:
        import webview
        if not _porta_disponivel(8050):
            print("\n  \u2716 Porta 8050 em uso. Feche a outra inst\u00e2ncia e tente novamente.\n")
            raise SystemExit(1)
        t = threading.Thread(target=iniciar_dash, daemon=True)
        t.start()
        time.sleep(1.5)
        webview.create_window(
            title=NOME_BASE,
            url="http://127.0.0.1:8050",
            width=1400, height=900,
            resizable=True, min_size=(800, 600),
        )
        webview.start()
    except ImportError:
        print("\n  pywebview n\u00e3o instalado \u2014 abrindo no navegador.")
        print("  Acesse: http://127.0.0.1:8050\n")
        app.run(debug=True, port=8050)


# Permite executar diretamente:  python main.py
if __name__ == '__main__':
    run()
