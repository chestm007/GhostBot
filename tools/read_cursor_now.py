"""
Versao non-interactive de find_anchor.py: le a posicao do cursor IMEDIATAMENTE
(sem esperar input). Voce posiciona o mouse e roda o script.
"""
import ctypes
from ctypes import wintypes
import win32gui
import win32process
import win32api
import pymem

pid = next((p.th32ProcessID for p in pymem.process.list_processes() if p.szExeFile == b'client.exe'), None)
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
client_rect = win32gui.GetClientRect(hwnd)
ww = client_rect[2] - client_rect[0]
wh = client_rect[3] - client_rect[1]

screen_x, screen_y = win32api.GetCursorPos()
pt = wintypes.POINT(screen_x, screen_y)
ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(pt))
cx, cy = pt.x, pt.y

print(f"Janela: {ww} x {wh}")
print(f"Cursor: screen ({screen_x}, {screen_y}) | client ({cx}, {cy})")
print()
print(f"Offset top-left:     ({cx}, {cy})")
print(f"Offset top-right:    ({ww - cx}, {cy})")
print(f"Offset bottom-left:  ({cx}, {wh - cy})")
print(f"Offset bottom-right: ({ww - cx}, {wh - cy})")
print(f"Offset CENTER:       ({cx - ww // 2:+d}, {cy - wh // 2:+d})  <-- pra elementos centralizados (char, etc)")
