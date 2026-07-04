"""
FULL CYCLE (DRY) — chains everything we validated, without actually selling:

  1. NAVIGATE to the NPC (surroundings: open panel -> search -> 1st result -> arrive)
  2. OPEN SELL (reset camera -> right-click NPC -> "Dialogue" -> "Sell Item")
  3. SELL (find "Sell" -> 30 clicks on slot 1)  [DRY: DON'T confirm]
  4. CLOSE dialog (Esc)
  5. RETURN to spot (open map -> bait + spot -> close map -> wait to arrive)

All via template+offset, no fixed coords. Set DRY_CONFIRM=False only when
you want to actually sell.
"""
import time

import cv2

from GhostBot.lib.math import linear_distance
from GhostBot.lib.tooling import get_client, match_template

MISC = r"C:\Bot\BotTO\src\GhostBot\Images\misc"

# --- Surroundings (navegacao) ---
SURR_TITLE_BMP = MISC + r"\surroundings_title.bmp"
TITLE_TO_SEARCH = (140, 347)
TITLE_TO_FIRST_RESULT = (-106, 70)
SEARCH_TERM = "Blacksmith"
NPC_LOCATION = (365, 1093)

# --- Janela Dialogue do NPC ---
DIALOGUE_BMP = MISC + r"\npc_dialogue_title.bmp"
DIALOGUE_TO_SELL_ITEM = (-114, 181)

# --- Dialog de venda ---
SELL_HEADER_BMP = MISC + r"\npc_sell_dialog_header.bmp"
HEADER_TO_SLOT1 = (-97, 43)
HEADER_TO_SELL_CONFIRM = (-76, 461)
SELL_COL_SPACING = 34.4      # grid 6 cols x 4 rows = 24 slots
SELL_ROW_SPACING = 35.333
SELL_START_SLOT = 1          # user chooses (1-24): sell from this onward, keep 1..N-1
SLOT_CLICKS = 30


def slot_pos(hdr, n):
    """Position of slot n (1-24) of the sell grid, anchored to the header."""
    idx = n - 1
    row, col = idx // 6, idx % 6
    return (int(hdr[0] + HEADER_TO_SLOT1[0] + col * SELL_COL_SPACING),
            int(hdr[1] + HEADER_TO_SLOT1[1] + row * SELL_ROW_SPACING))

# --- Map (return to spot) ---
MAP_TITLE_BMP = MISC + r"\map_title.bmp"
MAP_TO_SPOT = (-125, 297)
MAP_DUMMY_OFFSET = (60, 0)
SPOT_WORLD = (321, 1147)

ARRIVAL = 3
THRESHOLD = 0.70
STEP_DELAY = 2.0     # delay between activities (give the game time to finish each action)
DRY_CONFIRM = True   # True = DO NOT click the Sell confirm


def wait_arrival(client, target, timeout=60):
    t0 = time.time()
    last = None
    stat = None
    while time.time() - t0 < timeout:
        cur = client.location
        d = linear_distance(cur, target)
        print(f"    loc={cur} dist={d:.1f}")
        if d < ARRIVAL:
            print(f"    >>> ARRIVED (dist={d:.1f})")
            return True
        if last is not None and linear_distance(cur, last) < 1:
            if stat is None:
                stat = time.time()
            elif time.time() - stat > 5:
                print(f"    >>> stopped without arriving (dist={d:.1f})")
                return False
        else:
            stat = None
        last = cur
        time.sleep(1)
    print("    >>> TIMEOUT")
    return False


def navigate_to_npc(client):
    print("[1] NAVIGATE to the NPC")
    try:
        title_match = match_template(client, SURR_TITLE_BMP, threshold=THRESHOLD)
        title, score = title_match.center, title_match.score
    except SystemExit:
        title, score = None, 0.0
    if title is None:
        print(f"    panel closed (score {score:.3f}) -> opening")
        client.open_surroundings_ui()
        time.sleep(1.5)
        try:
            title_match = match_template(client, SURR_TITLE_BMP, threshold=THRESHOLD)
            title, score = title_match.center, title_match.score
        except SystemExit:
            title, score = None, 0.0
    if title is None:
        raise SystemExit(f"    FAILED: 'Surroundings' not found (score {score:.3f})")
    print(f"    'Surroundings' at {title} (score {score:.3f})")
    search = (title[0] + TITLE_TO_SEARCH[0], title[1] + TITLE_TO_SEARCH[1])
    result = (title[0] + TITLE_TO_FIRST_RESULT[0], title[1] + TITLE_TO_FIRST_RESULT[1])
    client.left_click(search)
    time.sleep(0.4)
    for _ in range(15):
        client.press_key('backspace')
    time.sleep(0.3)
    client.type_keys(SEARCH_TERM)
    time.sleep(1.0)
    client.left_click(result)
    if not wait_arrival(client, NPC_LOCATION):
        raise SystemExit("    FAILED: did not reach the NPC")
    print(f"    waiting for char to stop completely ({STEP_DELAY}s)...")
    time.sleep(STEP_DELAY)
    client.open_surroundings_ui()  # close panel
    time.sleep(STEP_DELAY)


def open_sell_dialog(client):
    print("[2] OPEN SELL")
    time.sleep(STEP_DELAY)            # deixa o char assentar antes
    client.reset_camera()
    time.sleep(STEP_DELAY)
    client.click_npc()
    time.sleep(STEP_DELAY)
    try:
        dlg_match = match_template(client, DIALOGUE_BMP, threshold=THRESHOLD)
        dlg, score = dlg_match.center, dlg_match.score
    except SystemExit:
        dlg, score = None, 0.0
    if dlg is None:
        raise SystemExit(f"    FAILED: 'Dialogue' not found (score {score:.3f})")
    sell_item = (dlg[0] + DIALOGUE_TO_SELL_ITEM[0], dlg[1] + DIALOGUE_TO_SELL_ITEM[1])
    print(f"    'Dialogue' at {dlg} (score {score:.3f}) -> Sell Item {sell_item}")
    client.left_click(sell_item)
    time.sleep(STEP_DELAY)
    try:
        hdr_match = match_template(client, SELL_HEADER_BMP, threshold=THRESHOLD)
        hdr, hscore = hdr_match.center, hdr_match.score
    except SystemExit:
        hdr, hscore = None, 0.0
    if hdr is None:
        raise SystemExit(f"    FAILED: sell dialog did not open (header score {hscore:.3f})")
    print(f"    sell dialog open (header {hdr} score {hscore:.3f})")
    return hdr


def sell_page(client, hdr):
    print("[3] SELL (DRY)" if DRY_CONFIRM else "[3] SELL")
    start = slot_pos(hdr, SELL_START_SLOT)
    confirm = (hdr[0] + HEADER_TO_SELL_CONFIRM[0], hdr[1] + HEADER_TO_SELL_CONFIRM[1])
    print(f"    initial slot {SELL_START_SLOT} at {start} | confirm {confirm} -> {SLOT_CLICKS} clicks")
    for _ in range(SLOT_CLICKS):
        client.left_click(start)
        time.sleep(0.2)
    if DRY_CONFIRM:
        print("    [DRY] not confirming the sale")
    else:
        client.left_click(confirm)
        time.sleep(1.0)
        print("    sale confirmed")
    print("[4] CLOSE dialog (Esc)")
    client.press_key('esc')
    time.sleep(STEP_DELAY)


def return_to_spot(client):
    print("[5] RETURN to spot")
    client.press_key('m')   # open map
    time.sleep(STEP_DELAY)
    try:
        title_match = match_template(client, MAP_TITLE_BMP, threshold=THRESHOLD)
        title, score = title_match.center, title_match.score
    except SystemExit:
        title, score = None, 0.0
    if title is None:
        client.press_key('m')
        time.sleep(STEP_DELAY)
        try:
            title_match = match_template(client, MAP_TITLE_BMP, threshold=THRESHOLD)
            title, score = title_match.center, title_match.score
        except SystemExit:
            title, score = None, 0.0
    if title is None:
        raise SystemExit(f"    FALHOU: mapa/'Map' nao achado (score {score:.3f})")
    spot = (title[0] + MAP_TO_SPOT[0], title[1] + MAP_TO_SPOT[1])
    dummy = (spot[0] + MAP_DUMMY_OFFSET[0], spot[1] + MAP_DUMMY_OFFSET[1])
    print(f"    'Map' em {title} (score {score:.3f}) -> spot {spot} | isca {dummy}")
    client.right_click(dummy)
    time.sleep(0.5)
    client.right_click(spot)
    time.sleep(0.5)
    client.press_key('m')   # close map
    if not wait_arrival(client, SPOT_WORLD):
        print("    WARNING: did not confirm arrival at spot")


def main():
    client = get_client()
    print(f"Window: {client.get_window_size()} | DRY_CONFIRM={DRY_CONFIRM}")
    print(f"Char at {client.location}")
    print()

    navigate_to_npc(client)
    hdr = open_sell_dialog(client)
    sell_page(client, hdr)
    return_to_spot(client)
    print("\n===== FULL CYCLE =====")


if __name__ == "__main__":
    main()
