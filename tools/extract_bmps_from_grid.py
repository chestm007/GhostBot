"""
Extrai BMPs dos items visiveis no grid do NPC, salva em Images/SELL/.

Cada cell do grid eh 35x26 px (6 col x 5 row do grid 211x129).
Pega o item nos 3 primeiros slots da row 0 e salva.
"""
import cv2
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

HEADER_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\npc_sell_dialog_header.bmp"
SELL_DIR = r"C:\Bot\BotTO\src\GhostBot\Images\SELL"
HEADER_TO_SLOT1 = (-90, +50)
HEADER_TO_SLOT30 = (+85, +153)

# Tamanho do crop por slot (deixa um pouco menor que o cell pra evitar bordas)
CROP_W = 22
CROP_H = 18

proc = next(iter(PymemProcess.list_clients()), None)
client = Win32ClientWindow(proc)
window_img = client.capture_window()

# Acha header
header_bmp = cv2.imread(HEADER_BMP, cv2.IMREAD_GRAYSCALE)
window_gray = window_img if len(window_img.shape) == 2 else cv2.cvtColor(window_img, cv2.COLOR_BGR2GRAY)
res = cv2.matchTemplate(window_gray, header_bmp, cv2.TM_CCOEFF_NORMED)
_, mv, _, ml = cv2.minMaxLoc(res)
print(f"Header: {mv:.3f} em {ml}")
hx = ml[0] + header_bmp.shape[1] // 2
hy = ml[1] + header_bmp.shape[0] // 2

# Slot 1 center
s1x = hx + HEADER_TO_SLOT1[0]
s1y = hy + HEADER_TO_SLOT1[1]

# Spacing entre slots (calculado de slot 1 -> slot 30 com 6 col 5 row)
COL_SPACING = (HEADER_TO_SLOT30[0] - HEADER_TO_SLOT1[0]) / 5  # 5 gaps
ROW_SPACING = (HEADER_TO_SLOT30[1] - HEADER_TO_SLOT1[1]) / 4  # 4 gaps
print(f"Slot 1 center: ({s1x},{s1y})  spacing col={COL_SPACING:.1f} row={ROW_SPACING:.1f}")

# Extrai 3 primeiros slots da row 0
nomes = ["SweetFuit", "GreenScarpPill", "Pork"]
for i, name in enumerate(nomes):
    cx = int(s1x + i * COL_SPACING)
    cy = int(s1y)
    x1 = cx - CROP_W // 2
    y1 = cy - CROP_H // 2
    x2 = x1 + CROP_W
    y2 = y1 + CROP_H
    crop = window_gray[y1:y2, x1:x2]
    out = f"{SELL_DIR}\\{name}.bmp"
    cv2.imwrite(out, crop)
    print(f"  Slot {i}: center=({cx},{cy})  crop={CROP_W}x{CROP_H}  -> {name}.bmp")
print("Pronto.")
