"""
Extract BMPs from visible items in the NPC grid, save to Images/SELL/.

Each grid cell is 35x26 px (6 cols x 5 rows of the 211x129 grid).
Takes the items in the first 3 slots of row 0 and saves them.
"""
from pathlib import Path

import cv2

from GhostBot.lib.tooling import get_client, match_template

HEADER_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\npc_sell_dialog_header.bmp"
SELL_DIR = Path(r"C:\Bot\BotTO\src\GhostBot\Images\SELL")
HEADER_TO_SLOT1 = (-90, +50)
HEADER_TO_SLOT30 = (+85, +153)

# Crop size per slot (slightly smaller than cell to avoid borders)
CROP_W = 22
CROP_H = 18

client = get_client()
window_img = client.capture_window()
header = match_template(client, HEADER_BMP)
window_gray = window_img if len(window_img.shape) == 2 else cv2.cvtColor(window_img, cv2.COLOR_BGR2GRAY)
print(f"Header: {header.score:.3f} em {header.top_left}")
hx, hy = header.center

# Slot 1 center
s1x = hx + HEADER_TO_SLOT1[0]
s1y = hy + HEADER_TO_SLOT1[1]

# Spacing between slots (calculated from slot 1 -> slot 30 with 6 cols 5 rows)
COL_SPACING = (HEADER_TO_SLOT30[0] - HEADER_TO_SLOT1[0]) / 5  # 5 gaps
ROW_SPACING = (HEADER_TO_SLOT30[1] - HEADER_TO_SLOT1[1]) / 4  # 4 gaps
print(f"Slot 1 center: ({s1x},{s1y})  spacing col={COL_SPACING:.1f} row={ROW_SPACING:.1f}")

# Extract first 3 slots of row 0
nomes = ["SweetFuit", "GreenScarpPill", "Pork"]
SELL_DIR.mkdir(parents=True, exist_ok=True)
for i, name in enumerate(nomes):
    cx = int(s1x + i * COL_SPACING)
    cy = int(s1y)
    x1 = cx - CROP_W // 2
    y1 = cy - CROP_H // 2
    x2 = x1 + CROP_W
    y2 = y1 + CROP_H
    crop = window_gray[y1:y2, x1:x2]
    out = SELL_DIR / f"{name}.bmp"
    cv2.imwrite(str(out), crop)
    print(f"  Slot {i}: center=({cx},{cy})  crop={CROP_W}x{CROP_H}  -> {name}.bmp")
print("Done.")
