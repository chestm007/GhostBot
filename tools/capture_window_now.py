"""Capture the TO window exactly as the bot sees it and save it to tmp_window_now.png."""
from __future__ import annotations

import cv2

from _shared import capture_window, get_client


client = get_client()
ww, wh = client.get_window_size()
print(f"Window: {ww} x {wh}")

img = capture_window(client, color=True)
out = r"C:\Bot\BotTO\tmp_window_now.png"
cv2.imwrite(out, img)
print(f"Saved to {out} | shape={img.shape}")
