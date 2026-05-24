"""
Teste: move o cursor FISICAMENTE pra (200, 309) e clica via mouse_event,
em vez de SendMessage com lparam.

Hipotese: o NPC Sell dialog usa posicao REAL do cursor pra detectar clicks
em items (nao a posicao do lparam do WM_LBUTTON).
"""
import time
import ctypes
from ctypes import wintypes
import win32api
import win32gui
import win32process
import win32con
import pymem

# Coord do primeiro item (computado: header center + offset slot1)
# Header detectado em (290, 234), offset (-90, +75) = (200, 309)
CLIENT_X, CLIENT_Y = 200, 309

# Acha janela do TO
pid = next((p.th32ProcessID for p in pymem.process.list_processes() if p.szExeFile == b'client.exe'), None)
if pid is None:
    raise SystemExit("client.exe nao encontrado")

def find_window():
    found = []
    def cb(hwnd, _):
        _, p = win32process.GetWindowThreadProcessId(hwnd)
        if p == pid and win32gui.IsWindowVisible(hwnd):
            found.append(hwnd)
    win32gui.EnumWindows(cb, None)
    return found[0] if found else None

hwnd = find_window()
print(f"HWND={hwnd}")

# Converte client coord pra screen coord
pt = wintypes.POINT(CLIENT_X, CLIENT_Y)
ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))
sx, sy = pt.x, pt.y
print(f"Client ({CLIENT_X},{CLIENT_Y}) -> Screen ({sx},{sy})")

print()
print("TIRA A MAO DO MOUSE -- vou mexer ele em 3s")
time.sleep(3)

print(f"Focando janela...")
try:
    win32gui.SetForegroundWindow(hwnd)
except Exception as e:
    print(f"  warning: {e}")
time.sleep(0.3)

print(f"SetCursorPos({sx},{sy})")
win32api.SetCursorPos((sx, sy))
time.sleep(0.5)

actual = win32api.GetCursorPos()
print(f"GetCursorPos = {actual}")
if actual != (sx, sy):
    print(f"  AVISO: cursor NAO foi pra ({sx},{sy}). SetCursorPos pode estar bloqueado.")

print("mouse_event LEFTDOWN + UP")
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.1)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

print("Done. O item moveu pro grid inferior?")
