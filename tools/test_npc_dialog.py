"""
Abre a janela do NPC (assumindo char ja em cima dele) pra inspecionar
o botao "Sell Item". Reset de camera + right-click no centro.
NAO vende nada -- so abre e captura.
"""
import time
import cv2
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

proc = next(iter(PymemProcess.list_clients()), None)
if proc is None:
    raise SystemExit("client.exe nao encontrado")
client = Win32ClientWindow(proc)
print("Window:", client.get_window_size())

print("Resetando camera...")
client.reset_camera()
time.sleep(1.5)

print("Right-click no NPC (centro da tela)...")
client.click_npc()
time.sleep(1.5)

out = r"C:\Bot\BotTO\tmp_npc_window.png"
cv2.imwrite(out, client.capture_window(color=True))
print("Screenshot salvo:", out)
