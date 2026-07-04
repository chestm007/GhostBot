"""Calibrate the System chat region for drop OCR."""
from __future__ import annotations

import os
import time

import cv2
import pytesseract

from _shared import get_client, match_template, screen_to_client
from test_ocr_chat import prep_gray_otsu, extract_item_names  # reuses treatment B

for _c in (r"C:\Program Files\Tesseract-OCR\tesseract.exe",
           r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
    if os.path.exists(_c):
        pytesseract.pytesseract.tesseract_cmd = _c
        break

ANCHOR_PATH = r"C:\Bot\BotTO\tmp_anchor_template.png"
COUNTDOWN = 7

client = get_client()
hwnd = client.window_handle

print("=" * 60)
print("  Leave MOUSE at the UPPER-RIGHT corner of the chat area")
print("  (where you want the reading to END), and wait for it to reach zero.")
print("=" * 60)
for i in range(COUNTDOWN, 0, -1):
    print(f"  reading in {i}... ", end="\r", flush=True)
    time.sleep(1)
print("  >>> LENDO AGORA <<<        ")

match = match_template(client, ANCHOR_PATH, threshold=0.0)
mx, my = screen_to_client(hwnd)

win_gray = client.capture_window()           # grayscale, as the bot uses
win_color = client.capture_window(color=True)
cap_h, cap_w = win_gray.shape[:2]

print(f"\ncaptura(cliente)={cap_w}x{cap_h}")
print(f"ancora: score={match.score:.3f}  top-left=({match.top_left[0]},{match.top_left[1]})")
print(f"mouse (coord janela): ({mx},{my})")

# rectangle: left+bottom come from the anchor; right+top come from the mouse
x1, y1, x2, y2 = match.top_left[0], my, mx, match.top_left[1]
if not (x2 > x1 and y2 > y1):
    print("\n(!) Invalid rectangle. The mouse needs to be ABOVE and to the RIGHT")
    print("    of the chat icons. Try again, positioning more up/right.")
    raise SystemExit(1)

print(f"\nOCR RECTANGLE: x1={x1} y1={y1} x2={x2} y2={y2}  (w={x2-x1} h={y2-y1})")
print(f">>> OFFSETS upper-right relative to anchor top-left: ({mx-match.top_left[0]}, {my-match.top_left[1]})")

# validate live: crop, process, OCR
crop = win_color[y1:y2, x1:x2]
cv2.imwrite(r"C:\Bot\BotTO\tmp_chat_calib.png", crop)
text = pytesseract.image_to_string(prep_gray_otsu(crop), config="--psm 6")
print("\n=== OCR of calibrated region (treatment B) ===")
print(text.strip())
print(f"\n-> ITEMS DETECTED: {extract_item_names(text) or '(none)'}")
print("\n(crop saved to tmp_chat_calib.png -- send it to me to verify)")
