"""
Simple sell loop (without item-by-item detection):
  1. Find the "Sell" title of the dialog ONCE (anchor)
  2. Click on slot 1 CLICKS times (the grid does reflow: the next item rises
     to slot 1; unsellable items don't appear)
  3. Click the "Sell" button at the bottom to confirm the sale  -- ONLY if DRY_RUN=False

Find the title only at the start (the item tooltip covers the title after,
so we can't re-search in the middle of the loop).

DO NOT modify production code.
"""
import time

from GhostBot.lib.tooling import find_template_center, get_client

SELL_HEADER_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\npc_sell_dialog_header.bmp"
HEADER_TO_SLOT1 = (-97, 43)          # Sell title -> slot 1
HEADER_TO_SELL_CONFIRM = (-76, 461)  # Sell title -> Sell button at bottom (confirm)
COL_SPACING = 34.4                   # grid 6 cols x 4 rows = 24 slots
ROW_SPACING = 35.333
START_SLOT = 2                       # sell from this slot onward, keep 1..N-1

CLICKS = 30
CLICK_DELAY = 0.2
DRY_RUN = True   # True = DO NOT confirm the sale (just move items to the lower grid)


def slot_pos(hdr, n):
    idx = n - 1
    row, col = idx // 6, idx % 6
    return (int(hdr[0] + HEADER_TO_SLOT1[0] + col * COL_SPACING),
            int(hdr[1] + HEADER_TO_SLOT1[1] + row * ROW_SPACING))


def main():
    client = get_client()

    hdr, score = find_template_center(client, SELL_HEADER_BMP, threshold=0.70)
    start = slot_pos(hdr, START_SLOT)
    confirm = (hdr[0] + HEADER_TO_SELL_CONFIRM[0], hdr[1] + HEADER_TO_SELL_CONFIRM[1])
    print(f"'Sell' title at {hdr} (score {score:.3f})")
    print(f"Starting slot {START_SLOT} at {start} | Confirm at {confirm}")
    print(f"Clicking slot {START_SLOT} {CLICKS}x (keeping slots 1..{START_SLOT-1})...")

    for i in range(CLICKS):
        client.left_click(start)
        time.sleep(CLICK_DELAY)

    if DRY_RUN:
        print(">>> DRY_RUN: DID NOT click the 'Sell' confirm. Check the items in the lower grid.")
    else:
        print(f"Confirming sale (click at {confirm})...")
        client.left_click(confirm)
        time.sleep(1.0)
        print(">>> Sale confirmed.")


if __name__ == "__main__":
    main()
