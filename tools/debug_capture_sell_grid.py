"""Captura a area do grid superior do dialog Sell e salva como PNG pra visualizar."""
import cv2
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

# Mesmas coords do test_sell_in_npc.py
GRID_X1, GRID_Y1 = 432, 281
GRID_X2, GRID_Y2 = 644, 410

proc = next(iter(PymemProcess.list_clients()), None)
client = Win32ClientWindow(proc)

window_img = client.capture_window()
grid = window_img[GRID_Y1:GRID_Y2, GRID_X1:GRID_X2]

# Salva o crop e a window inteira (pra comparar)
cv2.imwrite(r"C:\Bot\BotTO\tmp_sell_grid_crop.png", grid)
cv2.imwrite(r"C:\Bot\BotTO\tmp_sell_window_full.png", window_img)
print(f"Janela: {window_img.shape[1]}x{window_img.shape[0]}")
print(f"Grid crop: {grid.shape[1]}x{grid.shape[0]} salvo em tmp_sell_grid_crop.png")
print(f"Janela full salva em tmp_sell_window_full.png")
