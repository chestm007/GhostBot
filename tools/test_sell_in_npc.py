"""
Teste de venda no NPC -- VERSAO ROBUSTA (template matching pra achar dialog).

Fluxo:
  1. Acha o header 'Sell' do dialog via template matching de
     Images/misc/npc_sell_dialog_header.bmp
  2. A partir do header, computa posicoes de slot 1, slot 30,
     sell confirm e next page usando offsets capturados
  3. Pra cada pagina (max 3):
     - Screenshot do grid superior
     - Match cada BMP de Images/SELL/ na area do grid
     - Click cada match
     - Click Sell confirm (se DRY_RUN=False)
     - Click Next page (se DRY_RUN=False)

Dialog pode estar em QUALQUER posicao -- template matching encontra.
"""
import os
import time
import cv2
import numpy as np
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

# ---- Offsets relativos ao centro do header (capturados via read_cursor_now) ----
# Y do slot 1 ajustado -25 (era 75) -- captura inicial estava 1 row abaixo
HEADER_TO_SLOT1 = (-90, +50)
HEADER_TO_SLOT30 = (+85, +153)   # tambem ajustado -25 pra manter spacing
HEADER_TO_SELL_CONFIRM = (-69, +498)
HEADER_TO_NEXT_PAGE = (+98, +41)

# ---- Config ----
HEADER_BMP_PATH = r"C:\Bot\BotTO\src\GhostBot\Images\misc\npc_sell_dialog_header.bmp"
SELL_DIR = r"C:\Bot\BotTO\src\GhostBot\Images\SELL"
MAX_PAGES = 3
ITEM_MATCH_THRESHOLD = 0.85
HEADER_MATCH_THRESHOLD = 0.85
DEDUP_TOLERANCE = 15
DRY_RUN = True  # True = nao clica sell confirm nem next page


def find_header_center(window_img):
    """Acha o header do dialog Sell na janela. Retorna (cx, cy) ou None."""
    header_bmp = cv2.imread(HEADER_BMP_PATH, cv2.IMREAD_GRAYSCALE)
    if header_bmp is None:
        raise SystemExit(f"BMP do header nao encontrado em {HEADER_BMP_PATH}")
    window_gray = cv2.cvtColor(window_img, cv2.COLOR_BGR2GRAY) if len(window_img.shape) == 3 else window_img
    result = cv2.matchTemplate(window_gray, header_bmp, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    print(f"Header match score: {max_val:.3f} em {max_loc}")
    if max_val < HEADER_MATCH_THRESHOLD:
        return None
    h, w = header_bmp.shape[:2]
    return (max_loc[0] + w // 2, max_loc[1] + h // 2)


def load_sell_bmps():
    bmps = {}
    for fn in os.listdir(SELL_DIR):
        if not fn.lower().endswith(".bmp"):
            continue
        img = cv2.imread(os.path.join(SELL_DIR, fn), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            bmps[fn] = img
    return bmps


def find_sellable_in_grid(window_img, header_pos, sell_bmps):
    """Acha items de SELL/ no grid superior. Retorna lista de (cx, cy, item_name)."""
    hx, hy = header_pos
    s1x, s1y = hx + HEADER_TO_SLOT1[0], hy + HEADER_TO_SLOT1[1]
    s30x, s30y = hx + HEADER_TO_SLOT30[0], hy + HEADER_TO_SLOT30[1]
    # bounding box do grid superior com um pouco de margem (half slot)
    grid_x1 = s1x - 18
    grid_y1 = s1y - 13
    grid_x2 = s30x + 18
    grid_y2 = s30y + 13
    print(f"Grid area: ({grid_x1},{grid_y1}) -> ({grid_x2},{grid_y2}) size {grid_x2-grid_x1}x{grid_y2-grid_y1}")

    grid_area = window_img[grid_y1:grid_y2, grid_x1:grid_x2]
    if len(grid_area.shape) == 3:
        grid_area = cv2.cvtColor(grid_area, cv2.COLOR_BGR2GRAY)

    matches = []
    for item_name, item_img in sell_bmps.items():
        try:
            result = cv2.matchTemplate(grid_area, item_img, cv2.TM_CCOEFF_NORMED)
        except cv2.error:
            continue
        loc = np.where(result >= ITEM_MATCH_THRESHOLD)
        h, w = item_img.shape[:2]
        for pt in zip(*loc[::-1]):
            cx = grid_x1 + pt[0] + w // 2
            cy = grid_y1 + pt[1] + h // 2
            if not any(abs(cx - x) <= DEDUP_TOLERANCE and abs(cy - y) <= DEDUP_TOLERANCE
                       for x, y, _ in matches):
                matches.append((cx, cy, item_name))
    return matches


def main():
    proc = next(iter(PymemProcess.list_clients()), None)
    if proc is None:
        raise SystemExit("client.exe nao encontrado")
    client = Win32ClientWindow(proc)
    print(f"Window: {client.get_window_size()}")
    print(f"DRY_RUN: {DRY_RUN}")
    print()

    sell_bmps = load_sell_bmps()
    print(f"Carregados {len(sell_bmps)} BMPs de SELL/")
    print()
    print("Comecando em 3s...")
    time.sleep(3)

    # Acha header (uma vez -- assumimos dialog nao move durante execucao)
    window_img = client.capture_window()
    header_pos = find_header_center(window_img)
    if header_pos is None:
        print(">>> ERRO: Header do dialog nao encontrado. Dialog ta aberto?")
        return
    print(f"Header encontrado em {header_pos}")

    sell_confirm_pos = (header_pos[0] + HEADER_TO_SELL_CONFIRM[0],
                        header_pos[1] + HEADER_TO_SELL_CONFIRM[1])
    next_page_pos = (header_pos[0] + HEADER_TO_NEXT_PAGE[0],
                     header_pos[1] + HEADER_TO_NEXT_PAGE[1])
    print(f"Sell confirm: {sell_confirm_pos}")
    print(f"Next page: {next_page_pos}")

    for page in range(1, MAX_PAGES + 1):
        print(f"\n===== PAGINA {page}/{MAX_PAGES} =====")
        # re-screenshot pra refletir items na pagina atual
        window_img = client.capture_window()
        matches = find_sellable_in_grid(window_img, header_pos, sell_bmps)
        print(f"Items sellable encontrados: {len(matches)}")
        for x, y, name in matches:
            print(f"  - {name} em ({x}, {y})")
        matches.sort(key=lambda m: (-m[1], -m[0]))  # bottom-right -> top-left

        for x, y, name in matches:
            print(f"  Clicando {name} em ({x}, {y})")
            client.left_click((x, y))
            time.sleep(0.4)

        if matches:
            if DRY_RUN:
                print(f"  [DRY_RUN] PULA Sell confirm em {sell_confirm_pos}")
            else:
                print(f"  Clicando Sell confirm em {sell_confirm_pos}")
                client.left_click(sell_confirm_pos)
                time.sleep(1.5)
        else:
            print("  Nenhum item sellable nessa pagina.")

        if page < MAX_PAGES:
            if DRY_RUN:
                print(f"  [DRY_RUN] PULA Next page em {next_page_pos} -- abortando")
                break
            else:
                print(f"  Clicando Next page em {next_page_pos}")
                client.left_click(next_page_pos)
                time.sleep(1)

    print("\n===== FIM =====")


if __name__ == "__main__":
    main()
