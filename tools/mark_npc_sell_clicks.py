"""Mark where test_sell_in_npc would click, with the detected header and applied offsets."""
from __future__ import annotations

import cv2

from _shared import capture_window, get_client, load_gray_template


HEADER_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\npc_sell_dialog_header.bmp"
HEADER_TO_SLOT1 = (-90, +75)
HEADER_TO_SLOT30 = (+85, +178)
HEADER_TO_SELL_CONFIRM = (-69, +498)
HEADER_TO_NEXT_PAGE = (+98, +41)

client = get_client()
window_img = capture_window(client, color=True)

# Find header
header_bmp = load_gray_template(HEADER_BMP)
window_gray = cv2.cvtColor(window_img, cv2.COLOR_BGR2GRAY)
res = cv2.matchTemplate(window_gray, header_bmp, cv2.TM_CCOEFF_NORMED)
_, mv, _, ml = cv2.minMaxLoc(res)
print(f"Header match score: {mv:.3f} at top-left {ml}")
h, w = header_bmp.shape[:2]
hx = ml[0] + w // 2
hy = ml[1] + h // 2

# Draw rectangle on detected header (green) + cross on center
cv2.rectangle(window_img, ml, (ml[0] + w, ml[1] + h), (0, 255, 0), 2)
cv2.putText(window_img, f"HEADER (score {mv:.2f})", (ml[0], ml[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)


def mark(label, dx, dy, color):
    x = hx + dx
    y = hy + dy
    cv2.circle(window_img, (x, y), 10, color, 2)
    cv2.line(window_img, (x - 15, y), (x + 15, y), color, 1)
    cv2.line(window_img, (x, y - 15), (x, y + 15), color, 1)
    cv2.putText(window_img, label, (x + 15, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)


mark("slot 1", *HEADER_TO_SLOT1, (0, 255, 255))           # yellow
mark("slot 30", *HEADER_TO_SLOT30, (255, 0, 255))         # purple
mark("Sell confirm", *HEADER_TO_SELL_CONFIRM, (0, 0, 255)) # red
mark("Next page", *HEADER_TO_NEXT_PAGE, (255, 0, 0))      # blue

out = r"C:\Bot\BotTO\tmp_marked_npc_clicks.png"
cv2.imwrite(out, window_img)
print(f"Saved {out}")
