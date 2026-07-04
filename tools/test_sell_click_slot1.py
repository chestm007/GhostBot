"""
Test: find the "Sell" title of the sell dialog and click on SLOT 1
(anchor + offset, calibrated via cursor). DO NOT confirm the sale.

IMPORTANT: move the REAL mouse away from the items before running -- the item
tooltip covers the title and the template won't match.
"""
import time

from GhostBot.lib.tooling import find_template_center, get_client

SELL_HEADER_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\npc_sell_dialog_header.bmp"
HEADER_TO_SLOT1 = (-97, 43)   # titulo Sell -> slot 1 (calibrado via cursor)


def main():
    client = get_client()

    hdr, score = find_template_center(client, SELL_HEADER_BMP, threshold=0.70)
    slot1 = (hdr[0] + HEADER_TO_SLOT1[0], hdr[1] + HEADER_TO_SLOT1[1])
    print(f"'Sell' title at {hdr} (score {score:.3f}) -> slot 1 at {slot1} -- clicking...")
    client.left_click(slot1)
    time.sleep(0.5)
    print(">>> Clicked. Check if the slot 1 item moved to the lower grid.")


if __name__ == "__main__":
    main()
