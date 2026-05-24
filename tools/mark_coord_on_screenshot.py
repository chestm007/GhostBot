"""Marca coords no screenshot da janela pra ver onde elas caem visualmente."""
import cv2
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

# Coords a marcar (client coord)
POINTS = [
    ((450, 294), "slot 1 (que voce capturou)", (0, 255, 255)),     # amarelo
    ((626, 397), "slot 30 (que voce capturou)", (255, 0, 255)),    # roxo
    ((479, 713), "Sell confirm", (0, 0, 255)),                     # vermelho
    ((643, 257), "Next page", (255, 0, 0)),                        # azul
    ((275, 417), "Sell button (menu NPC)", (0, 255, 0)),           # verde
]

proc = next(iter(PymemProcess.list_clients()), None)
client = Win32ClientWindow(proc)
img = client.capture_window()

for (x, y), label, color in POINTS:
    cv2.circle(img, (x, y), 8, color, 2)
    cv2.line(img, (x - 15, y), (x + 15, y), color, 1)
    cv2.line(img, (x, y - 15), (x, y + 15), color, 1)
    cv2.putText(img, label, (x + 15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

out = r"C:\Bot\BotTO\tmp_marked_window.png"
cv2.imwrite(out, img)
print(f"Salvo {out} -- janela {img.shape[1]}x{img.shape[0]}")
