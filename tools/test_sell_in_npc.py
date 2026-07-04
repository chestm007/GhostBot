"""
Sell test in NPC -- ROBUST VERSION (template matching to find dialog).

Flow:
  1. Find the 'Sell' header of the dialog via template matching of
     Images/misc/npc_sell_dialog_header.bmp
  2. From the header, compute slot 1, slot 30,
     sell confirm and next page positions using captured offsets
  3. For each page (max 3):
     - Screenshot the top grid
     - Match each BMP from Images/SELL/ in the grid area
     - Click each match
     - Click Sell confirm (if DRY_RUN=False)
     - Click Next page (if DRY_RUN=False)

Dialog can be in ANY position -- template matching finds it.
"""
import os
import time
import cv2
import numpy as np

from GhostBot.lib.tooling import get_client, match_template

# ---- Offsets relative to header center (captured via read_cursor_now) ----
# Y of slot 1 adjusted -25 (was 75) -- initial capture was 1 row below
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
    """Find SELL/ items in the top grid. Returns list of (cx, cy, item_name)."""
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
    client = get_client()
    print(f"Window: {client.get_window_size()}")
    print(f"DRY_RUN: {DRY_RUN}")
    print()

    sell_bmps = load_sell_bmps()
    print(f"Loaded {len(sell_bmps)} BMPs from SELL/")
    print()
    print(f"Starting in 3s...")
    time.sleep(3)

    # Find header (once -- we assume dialog doesn't move during execution)
    header_pos = match_template(client, HEADER_BMP_PATH, threshold=HEADER_MATCH_THRESHOLD).center
    print(f"Header found at {header_pos}")

    sell_confirm_pos = (header_pos[0] + HEADER_TO_SELL_CONFIRM[0],
                        header_pos[1] + HEADER_TO_SELL_CONFIRM[1])
    next_page_pos = (header_pos[0] + HEADER_TO_NEXT_PAGE[0],
                     header_pos[1] + HEADER_TO_NEXT_PAGE[1])
    print(f"Sell confirm: {sell_confirm_pos}")
    print(f"Next page: {next_page_pos}")

    for page in range(1, MAX_PAGES + 1):
        print(f"\n===== PAGINA {page}/{MAX_PAGES} =====")
        # re-screenshot to reflect items on the current page
        window_img = client.capture_window()
        matches = find_sellable_in_grid(window_img, header_pos, sell_bmps)
        print(f"Sellable items found: {len(matches)}")
        for x, y, name in matches:
            print(f"  - {name} em ({x}, {y})")
        matches.sort(key=lambda m: (-m[1], -m[0]))  # bottom-right -> top-left

        for x, y, name in matches:
            print(f"  Clicando {name} em ({x}, {y})")
            client.left_click((x, y))
            time.sleep(0.4)

        if matches:
            if DRY_RUN:
                print(f"  [DRY_RUN] SKIPPING Sell confirm at {sell_confirm_pos}")
            else:
                print(f"  Clicking Sell confirm at {sell_confirm_pos}")
                client.left_click(sell_confirm_pos)
                time.sleep(1.5)
        else:
            print(f"  No sellable items on this page.")

        if page < MAX_PAGES:
            if DRY_RUN:
                print(f"  [DRY_RUN] SKIPPING Next page at {next_page_pos} -- aborting")
                break
            else:
                print(f"  Clicking Next page at {next_page_pos}")
                client.left_click(next_page_pos)
                time.sleep(1)

    print("\n===== END =====")


if __name__ == "__main__":
    main()
