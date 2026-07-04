"""
Do char em cima do NPC -> abre o dialog de VENDA (com os grids).

  1. reset_camera
  2. right-click no NPC (abre a janela Dialogue)
  3. acha "Sell Item" via template (sell_items_button.bmp) e clica
  4. confirma que o dialog de venda abriu, achando o header
     (npc_sell_dialog_header.bmp)

NAO vende nada -- so abre o dialog e confirma.
"""
import time

import cv2

from GhostBot.lib.tooling import get_client

MISC = r"C:\Bot\BotTO\src\GhostBot\Images\misc"
DIALOGUE_BMP = MISC + r"\npc_dialogue_title.bmp"   # ancora: titulo "Dialogue"
SELL_HEADER_BMP = MISC + r"\npc_sell_dialog_header.bmp"

# offset do titulo "Dialogue" -> botao "Sell Item" (calibrado via cursor)
DIALOGUE_TO_SELL_ITEM = (-114, 181)

# True = pula reset_camera + click_npc (assume Dialogue JA aberto, ex: pra testar arrastado)
SKIP_OPEN = False


def find_center(client, bmp_path, thr):
    win = client.capture_window()  # grayscale
    bmp = cv2.imread(bmp_path, cv2.IMREAD_GRAYSCALE)
    if bmp is None:
        raise SystemExit(f"BMP nao encontrado: {bmp_path}")
    res = cv2.matchTemplate(win, bmp, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(res)
    h, w = bmp.shape[:2]
    if mv < thr:
        return None, mv
    return (ml[0] + w // 2, ml[1] + h // 2), mv


def main():
    client = get_client()


    if SKIP_OPEN:
        print("SKIP_OPEN=True: assumindo Dialogue ja aberto (arrastado).")
    else:
        print("Reset de camera...")
        client.reset_camera()
        time.sleep(1.5)

        print("Right-click no NPC (centro)...")
        client.click_npc()
        time.sleep(1.5)

    dlg, score = find_center(client, DIALOGUE_BMP, 0.70)
    if dlg is None:
        cv2.imwrite(r"C:\Bot\BotTO\tmp_sell_dialog.png", client.capture_window(color=True))
        raise SystemExit(f">>> titulo 'Dialogue' nao achado (score {score:.3f}). Janela do NPC abriu?")
    sell_item_pos = (dlg[0] + DIALOGUE_TO_SELL_ITEM[0], dlg[1] + DIALOGUE_TO_SELL_ITEM[1])
    print(f"Ancora 'Dialogue' em {dlg} (score {score:.3f}) -> 'Sell Item' em {sell_item_pos} -- clicando...")
    client.left_click(sell_item_pos)
    time.sleep(1.5)

    cv2.imwrite(r"C:\Bot\BotTO\tmp_sell_dialog.png", client.capture_window(color=True))
    hpos, hscore = find_center(client, SELL_HEADER_BMP, 0.80)
    if hpos:
        print(f">>> DIALOG DE VENDA ABERTO! header em {hpos} (score {hscore:.3f})")
    else:
        print(f">>> Header do dialog nao achado (score {hscore:.3f}). Ver tmp_sell_dialog.png")


if __name__ == "__main__":
    main()
