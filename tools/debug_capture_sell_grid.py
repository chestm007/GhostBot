"""Capture the top grid area of the Sell dialog and save as PNG for viewing."""
import cv2

from GhostBot.lib.tooling import get_client

# Same coords as test_sell_in_npc.py
GRID_X1, GRID_Y1 = 432, 281
GRID_X2, GRID_Y2 = 644, 410

client = get_client()

window_img = client.capture_window()
grid = window_img[GRID_Y1:GRID_Y2, GRID_X1:GRID_X2]

# Save the crop and the full window (for comparison)
cv2.imwrite(r"C:\Bot\BotTO\tmp_sell_grid_crop.png", grid)
cv2.imwrite(r"C:\Bot\BotTO\tmp_sell_window_full.png", window_img)
print(f"Janela: {window_img.shape[1]}x{window_img.shape[0]}")
print(f"Grid crop: {grid.shape[1]}x{grid.shape[0]} saved to tmp_sell_grid_crop.png")
print(f"Full window saved to tmp_sell_window_full.png")
