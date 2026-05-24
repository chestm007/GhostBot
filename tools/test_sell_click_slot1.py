"""
Teste: acha o titulo "Sell" do dialog de venda e clica no SLOT 1
(ancora + offset, calibrado via cursor). NAO confirma venda.

IMPORTANTE: tira o mouse REAL de cima dos itens antes de rodar -- o tooltip
do item cobre o titulo e o template nao bate.
"""
import time
import cv2
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

SELL_HEADER_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\npc_sell_dialog_header.bmp"
HEADER_TO_SLOT1 = (-97, 43)   # titulo Sell -> slot 1 (calibrado via cursor)


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
                         "Mouse real esta cobrindo o titulo? Dialog aberto?")
    slot1 = (hdr[0] + HEADER_TO_SLOT1[0], hdr[1] + HEADER_TO_SLOT1[1])
    print(f"Titulo 'Sell' em {hdr} (score {score:.3f}) -> slot 1 em {slot1} -- clicando...")
    client.left_click(slot1)
    time.sleep(0.5)
    print(">>> Clicou. Confere se o item do slot 1 desceu pro grid de baixo.")


if __name__ == "__main__":
    main()
