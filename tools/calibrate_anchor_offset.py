"""
Calibra um OFFSET ancorado: acha uma ancora (BMP) na tela via template E
le a posicao do cursor NO MESMO instante, e imprime
    offset = cursor - centro_da_ancora

Uso:
    python tools/calibrate_anchor_offset.py <caminho_do_bmp>
    (default = npc_dialogue_title.bmp)

Posicione o mouse no elemento alvo (ex: botao "Sell Item") com o painel
da ancora ABERTO, depois rode. O offset sai pronto pra usar como
    pos_alvo = centro_ancora + offset
que funciona em qualquer posicao do painel (o template acha a ancora).
"""
import sys
import ctypes
from ctypes import wintypes
import cv2
import win32api
import win32gui
import win32process
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

DEFAULT_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\npc_dialogue_title.bmp"
THRESHOLD = 0.70


def main():
    bmp_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BMP

    proc = next(iter(PymemProcess.list_clients()), None)
    if proc is None:
        raise SystemExit("client.exe nao encontrado")
    client = Win32ClientWindow(proc)
    hwnd = client.window_handle

    # 1) ancora via template (em coords da CAPTURA)
    win = client.capture_window()  # grayscale
    bmp = cv2.imread(bmp_path, cv2.IMREAD_GRAYSCALE)
    if bmp is None:
        raise SystemExit(f"BMP nao encontrado: {bmp_path}")
    res = cv2.matchTemplate(win, bmp, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(res)
    h, w = bmp.shape[:2]
    ax, ay = ml[0] + w // 2, ml[1] + h // 2

    # 2) cursor em coords CLIENT
    sx, sy = win32api.GetCursorPos()
    pt = wintypes.POINT(sx, sy)
    ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(pt))
    cx, cy = pt.x, pt.y

    name = bmp_path.replace("\\", "/").split("/")[-1]
    print(f"Ancora '{name}': centro=({ax},{ay})  score={mv:.3f}  "
          f"{'OK' if mv >= THRESHOLD else '<<< ABAIXO DO THRESHOLD!'}")
    print(f"Cursor: client=({cx},{cy})")
    print(f">>> OFFSET (cursor - ancora) = ({cx - ax}, {cy - ay})")


if __name__ == "__main__":
    main()
