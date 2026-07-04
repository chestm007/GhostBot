"""Mark coords on a screenshot of the TO window to see where they fall visually."""
from __future__ import annotations

import cv2

from _shared import capture_window, get_client


POINTS = [
    ((450, 294), "slot 1 (that you captured)", (0, 255, 255)),     # yellow
    ((626, 397), "slot 30 (that you captured)", (255, 0, 255)),    # purple
    ((479, 713), "Sell confirm", (0, 0, 255)),                     # red
    ((643, 257), "Next page", (255, 0, 0)),                        # blue
    ((275, 417), "Sell button (NPC menu)", (0, 255, 0)),           # green
]

client = get_client()
img = capture_window(client)

for (x, y), label, color in POINTS:
    cv2.circle(img, (x, y), 8, color, 2)
    cv2.line(img, (x - 15, y), (x + 15, y), color, 1)
    cv2.line(img, (x, y - 15), (x, y + 15), color, 1)
    cv2.putText(img, label, (x + 15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

out = r"C:\Bot\BotTO\tmp_marked_window.png"
cv2.imwrite(out, img)
print(f"Saved {out} -- window {img.shape[1]}x{img.shape[0]}")
