"""
Ferramenta de descoberta de "anchor" pra elementos da UI do TO.

Voce posiciona o mouse em cima de um elemento (botao, campo, etc.),
volta no terminal, aperta ENTER. O script le:
- Posicao do cursor (client coord, relativa a janela)
- Tamanho da janela do TO
E calcula o offset de cada canto -- mostra qual canto e o "anchor"
mais provavel (o que tiver o menor offset).
"""
import ctypes
from ctypes import wintypes
import win32gui
import win32process
import win32api
import pymem

pid = None
for proc in pymem.process.list_processes():
    if proc.szExeFile == b'client.exe':
        pid = proc.th32ProcessID
        break
if pid is None:
    raise SystemExit("client.exe nao encontrado")

def find_window():
    found = []
    def cb(hwnd, _):
        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
        if found_pid == pid and win32gui.IsWindowVisible(hwnd):
            found.append(hwnd)
    win32gui.EnumWindows(cb, None)
    return found[0] if found else None

hwnd = find_window()
if hwnd is None:
    raise SystemExit("janela do TO nao encontrada")

# Tamanho client
client_rect = win32gui.GetClientRect(hwnd)
ww = client_rect[2] - client_rect[0]
wh = client_rect[3] - client_rect[1]

print("=" * 60)
print(f"  Janela TO: {ww} x {wh}")
print("=" * 60)
print()
print("  POSICIONA SEU MOUSE no elemento que voce quer (sem clicar),")
print("  depois volta aqui e aperta ENTER.")
input("\nApertou? Le agora: ")

# Le posicao na tela e converte pra client
screen_x, screen_y = win32api.GetCursorPos()
pt = wintypes.POINT(screen_x, screen_y)
ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(pt))
cx, cy = pt.x, pt.y

print()
print(f"Cursor: screen ({screen_x}, {screen_y}) | client ({cx}, {cy})")
print(f"Janela: {ww} x {wh}")
print()
print("Offset de cada canto:")
offsets = {
    'top-left':     (cx, cy),
    'top-right':    (ww - cx, cy),
    'bottom-left':  (cx, wh - cy),
    'bottom-right': (ww - cx, wh - cy),
}
for corner, (ox, oy) in offsets.items():
    print(f"  {corner:13s}: ({ox:+5d}, {oy:+5d})  -- distancia: {abs(ox)+abs(oy)}")

# Sugere anchor: o canto com menor soma de offsets absolutos
best = min(offsets.items(), key=lambda kv: abs(kv[1][0]) + abs(kv[1][1]))
print()
print(f">>> ANCHOR provavel: {best[0]} com offset {best[1]}")
print()
print("Formula sugerida pro código:")
corner, (ox, oy) = best
if corner == 'top-left':
    print(f"  pos = ({ox}, {oy})")
elif corner == 'top-right':
    print(f"  pos = (window_width - {ox}, {oy})")
elif corner == 'bottom-left':
    print(f"  pos = ({ox}, window_height - {oy})")
elif corner == 'bottom-right':
    print(f"  pos = (window_width - {ox}, window_height - {oy})")
