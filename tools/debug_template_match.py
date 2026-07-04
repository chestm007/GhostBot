"""
Run template matching of minimap_surroundings.bmp on a screenshot and draw
a RED rectangle around the match, saving the result.

Used for debugging: we can VISUALLY see if the template is finding the right button
or matching in the wrong place (false positive).
"""
import cv2
import numpy as np
from pathlib import Path

SCREENSHOT = Path("C:/Bot/BotTO/tmp_clipboard.png")
TEMPLATE = Path("C:/Bot/BotTO/src/GhostBot/Images/misc/minimap_surroundings.bmp")
OUTPUT = Path("C:/Bot/BotTO/tmp_match_debug.png")

img_color = cv2.imread(str(SCREENSHOT))
if img_color is None:
    raise SystemExit(f"Could not read {SCREENSHOT}")
img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)

template = cv2.imread(str(TEMPLATE), cv2.IMREAD_GRAYSCALE)
if template is None:
    raise SystemExit(f"Could not read {TEMPLATE}")

th, tw = template.shape[:2]
print(f"Screenshot: {img_color.shape[1]}x{img_color.shape[0]}")
print(f"Template:   {tw}x{th}")

result = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
print(f"Best match score: {max_val:.3f}")
print(f"Best match top-left: {max_loc}")

center = (max_loc[0] + tw // 2, max_loc[1] + th // 2)
print(f"Center (where bot clicks): {center}")

# Draw red rectangle on match
top_left = max_loc
bottom_right = (top_left[0] + tw, top_left[1] + th)
cv2.rectangle(img_color, top_left, bottom_right, (0, 0, 255), 3)
# Draw cross on center
cv2.line(img_color, (center[0] - 10, center[1]), (center[0] + 10, center[1]), (0, 255, 255), 2)
cv2.line(img_color, (center[0], center[1] - 10), (center[0], center[1] + 10), (0, 255, 255), 2)

# Also show TOP 5 matches (there may be false positives competing)
print("\nTop 5 matches (descending score):")
flat = result.flatten()
top_indices = np.argpartition(flat, -5)[-5:]
top_indices = top_indices[np.argsort(-flat[top_indices])]
for idx in top_indices:
    y, x = np.unravel_index(idx, result.shape)
    print(f"  score={result[y,x]:.3f}  top-left=({x},{y})  center=({x+tw//2},{y+th//2})")

cv2.imwrite(str(OUTPUT), img_color)
print(f"\nSaved to {OUTPUT}")
