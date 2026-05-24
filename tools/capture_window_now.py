"""
Captura a janela do TO EXATAMENTE como o bot a ve (via client.capture_window)
e salva em tmp_window_now.png. Usado pra inspecionar a UI e definir
templates/offsets (mesmo esquema do dialog de venda do NPC).
"""
import cv2
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

proc = next(iter(PymemProcess.list_clients()), None)
if proc is None:
    raise SystemExit("client.exe nao encontrado")

client = Win32ClientWindow(proc)
ww, wh = client.get_window_size()
print(f"Window: {ww} x {wh}")

img = client.capture_window(color=True)
out = r"C:\Bot\BotTO\tmp_window_now.png"
cv2.imwrite(out, img)
print(f"Salvo em {out} | shape={img.shape}")
