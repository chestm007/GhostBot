"""Debug: mostra o MAX SCORE de match pra cada BMP em SELL/ contra o grid."""
import os
import cv2
import numpy as np
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

HEADER_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\npc_sell_dialog_header.bmp"
SELL_DIR = r"C:\Bot\BotTO\src\GhostBot\Images\SELL"
HEADER_TO_SLOT1 = (-90, +75)
HEADER_TO_SLOT30 = (+85, +178)

proc = next(iter(PymemProcess.list_clients()), None)
client = Win32ClientWindow(proc)
window_img = client.capture_window()

# Acha header
header_bmp = cv2.imread(HEADER_BMP, cv2.IMREAD_GRAYSCALE)
window_gray = window_img if len(window_img.shape) == 2 else cv2.cvtColor(window_img, cv2.COLOR_BGR2GRAY)
print(f"Window shape: {window_img.shape}, channels={1 if len(window_img.shape)==2 else window_img.shape[2]}")
res = cv2.matchTemplate(window_gray, header_bmp, cv2.TM_CCOEFF_NORMED)
_, max_val, _, max_loc = cv2.minMaxLoc(res)
print(f"Header match: {max_val:.3f} em {max_loc}")
h, w = header_bmp.shape[:2]
hx, hy = max_loc[0] + w // 2, max_loc[1] + h // 2

# Computa grid
s1 = (hx + HEADER_TO_SLOT1[0], hy + HEADER_TO_SLOT1[1])
s30 = (hx + HEADER_TO_SLOT30[0], hy + HEADER_TO_SLOT30[1])
gx1, gy1 = s1[0] - 18, s1[1] - 13
gx2, gy2 = s30[0] + 18, s30[1] + 13
grid = window_gray[gy1:gy2, gx1:gx2]
print(f"Grid: ({gx1},{gy1}) -> ({gx2},{gy2}) size {grid.shape[1]}x{grid.shape[0]}")

# Salva grid
cv2.imwrite(r"C:\Bot\BotTO\tmp_npc_grid.png", grid)
print("Grid salvo em tmp_npc_grid.png")

print("\nScore de match pra cada BMP:")
results = []
for fn in sorted(os.listdir(SELL_DIR)):
    if not fn.lower().endswith(".bmp"):
        continue
    item = cv2.imread(os.path.join(SELL_DIR, fn), cv2.IMREAD_GRAYSCALE)
    if item is None:
        continue
    try:
        r = cv2.matchTemplate(grid, item, cv2.TM_CCOEFF_NORMED)
        _, mv, _, ml = cv2.minMaxLoc(r)
        results.append((mv, fn, ml, item.shape))
    except cv2.error as e:
        results.append((-1, fn, None, item.shape))

# ordena por score
results.sort(reverse=True)
for score, fn, ml, shape in results:
    print(f"  {score:.3f}  {fn:25s}  shape={shape}  loc={ml}")
