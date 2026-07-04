"""Debug: show the MAX match score for each BMP in SELL/ against the grid."""
from pathlib import Path
import os

import cv2

from GhostBot.lib.tooling import get_client, match_template

HEADER_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\npc_sell_dialog_header.bmp"
SELL_DIR = Path(r"C:\Bot\BotTO\src\GhostBot\Images\SELL")
HEADER_TO_SLOT1 = (-90, +75)
HEADER_TO_SLOT30 = (+85, +178)

client = get_client()
window_img = client.capture_window()
header = match_template(client, HEADER_BMP)
window_gray = window_img if len(window_img.shape) == 2 else cv2.cvtColor(window_img, cv2.COLOR_BGR2GRAY)
print(f"Window shape: {window_img.shape}, channels={1 if len(window_img.shape)==2 else window_img.shape[2]}")
print(f"Header match: {header.score:.3f} em {header.top_left}")
hx, hy = header.center

# Compute grid
s1 = (hx + HEADER_TO_SLOT1[0], hy + HEADER_TO_SLOT1[1])
s30 = (hx + HEADER_TO_SLOT30[0], hy + HEADER_TO_SLOT30[1])
gx1, gy1 = s1[0] - 18, s1[1] - 13
gx2, gy2 = s30[0] + 18, s30[1] + 13
grid = window_gray[gy1:gy2, gx1:gx2]
print(f"Grid: ({gx1},{gy1}) -> ({gx2},{gy2}) size {grid.shape[1]}x{grid.shape[0]}")

# Save grid
cv2.imwrite(r"C:\Bot\BotTO\tmp_npc_grid.png", grid)
print("Grid saved to tmp_npc_grid.png")

print("\nMatch score for each BMP:")
results = []
for bmp_path in sorted(SELL_DIR.glob('*.bmp')):
    item = cv2.imread(str(bmp_path), cv2.IMREAD_GRAYSCALE)
    if item is None:
        continue
    try:
        r = cv2.matchTemplate(grid, item, cv2.TM_CCOEFF_NORMED)
        _, mv, _, ml = cv2.minMaxLoc(r)
        results.append((mv, bmp_path.name, ml, item.shape))
    except cv2.error:
        results.append((-1, bmp_path.name, None, item.shape))

# ordered by score
results.sort(reverse=True)
for score, fn, ml, shape in results:
    print(f"  {score:.3f}  {fn:25s}  shape={shape}  loc={ml}")
