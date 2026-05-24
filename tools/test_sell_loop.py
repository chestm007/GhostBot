"""
Loop simples de venda (sem deteccao item-a-item):
  1. Acha o titulo "Sell" do dialog UMA vez (ancora)
  2. Clica no slot 1 CLICKS vezes (o grid faz reflow: o proximo item sobe
     pro slot 1; invendiveis nem aparecem)
  3. Clica no botao "Sell" de baixo pra confirmar a venda  -- SO se DRY_RUN=False

Acha o titulo so no comeco (o tooltip do item cobre o titulo depois,
entao nao da pra re-procurar no meio do loop).

NAO mexe no codigo de producao.
"""
import time
import cv2
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

SELL_HEADER_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\npc_sell_dialog_header.bmp"
HEADER_TO_SLOT1 = (-97, 43)          # titulo Sell -> slot 1
HEADER_TO_SELL_CONFIRM = (-76, 461)  # titulo Sell -> botao Sell de baixo (confirmar)
COL_SPACING = 34.4                   # grid 6 col x 4 linhas = 24 slots
ROW_SPACING = 35.333
START_SLOT = 2                       # vende deste slot em diante, mantem 1..N-1

CLICKS = 30
CLICK_DELAY = 0.2
DRY_RUN = True   # True = NAO confirma a venda (so move itens pro grid de baixo)


def slot_pos(hdr, n):
    idx = n - 1
    row, col = idx // 6, idx % 6
    return (int(hdr[0] + HEADER_TO_SLOT1[0] + col * COL_SPACING),
            int(hdr[1] + HEADER_TO_SLOT1[1] + row * ROW_SPACING))


def find_header(client, thr=0.70):
    win = client.capture_window()
    bmp = cv2.imread(SELL_HEADER_BMP, cv2.IMREAD_GRAYSCALE)
    res = cv2.matchTemplate(win, bmp, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(res)
    h, w = bmp.shape[:2]
    if mv < thr:
        return None, mv
    return (ml[0] + w // 2, ml[1] + h // 2), mv


def main():
    proc = next(iter(PymemProcess.list_clients()), None)
    if proc is None:
        raise SystemExit("client.exe nao encontrado")
    client = Win32ClientWindow(proc)

    hdr, score = find_header(client)
    if hdr is None:
        raise SystemExit(f">>> titulo 'Sell' nao achado (score {score:.3f}). "
                         "Dialog aberto? Mouse real cobrindo o titulo?")
    start = slot_pos(hdr, START_SLOT)
    confirm = (hdr[0] + HEADER_TO_SELL_CONFIRM[0], hdr[1] + HEADER_TO_SELL_CONFIRM[1])
    print(f"Titulo 'Sell' em {hdr} (score {score:.3f})")
    print(f"Slot inicial {START_SLOT} em {start} | Confirmar em {confirm}")
    print(f"Clicando slot {START_SLOT} {CLICKS}x (mantem slots 1..{START_SLOT-1})...")

    for i in range(CLICKS):
        client.left_click(start)
        time.sleep(CLICK_DELAY)

    if DRY_RUN:
        print(">>> DRY_RUN: NAO clicou o 'Sell' de confirmar. Confere os itens no grid de baixo.")
    else:
        print(f"Confirmando venda (clique em {confirm})...")
        client.left_click(confirm)
        time.sleep(1.0)
        print(">>> Venda confirmada.")


if __name__ == "__main__":
    main()
