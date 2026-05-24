"""
Testa diferentes formas de mandar um click numa coord da janela do TO.
Usa as mesmas APIs que o bot.

USO:
  python tools\test_click_methods.py            # testa todos os metodos
  python tools\test_click_methods.py SENDMSG    # testa so SendMessage (igual ao bot atual)
  python tools\test_click_methods.py POSTMSG    # testa PostMessage (assincrono)
  python tools\test_click_methods.py INPUT      # testa SendInput (simula hardware)
"""
import sys
import time
import ctypes
from ctypes import wintypes
import win32api
import win32gui
import win32process
import win32con
import pymem

# Coord pra clicar (botao surroundings) -- coord REAL onde o botao esta visualmente
# (medida via where_is_cursor.py, nao a coord do template match que tinha 30px de offset)
CLICK_X, CLICK_Y = 1551, 60

# Acha PID do client.exe
pid = None
for proc in pymem.process.list_processes():
    if proc.szExeFile == b'client.exe':
        pid = proc.th32ProcessID
        break
if pid is None:
    raise SystemExit("client.exe nao encontrado")
print(f"client.exe PID={pid}")

# Acha janela
def enum_callback(hwnd, results):
    _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
    if found_pid == pid and win32gui.IsWindowVisible(hwnd):
        results.append(hwnd)
windows = []
win32gui.EnumWindows(enum_callback, windows)
if not windows:
    raise SystemExit(f"Nenhuma janela do PID {pid} encontrada")
hwnd = windows[0]
print(f"Janela handle: {hwnd}")
print(f"Title: {win32gui.GetWindowText(hwnd)}")

# Pega tamanho client area
client_rect = win32gui.GetClientRect(hwnd)
print(f"Client rect: {client_rect}  (width={client_rect[2]-client_rect[0]}, height={client_rect[3]-client_rect[1]})")
print(f"Clicando em: ({CLICK_X}, {CLICK_Y})")

method = sys.argv[1].upper() if len(sys.argv) > 1 else 'ALL'

def sendmsg():
    print("\n[SENDMSG] Usando win32gui.SendMessage (igual ao bot atual)...")
    lparam = win32api.MAKELONG(CLICK_X, CLICK_Y)
    win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
    time.sleep(0.1)
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
    print("[SENDMSG] enviado. Olha o jogo agora -- abriu surroundings?")

def postmsg():
    print("\n[POSTMSG] Usando win32gui.PostMessage (assincrono)...")
    lparam = win32api.MAKELONG(CLICK_X, CLICK_Y)
    win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
    time.sleep(0.1)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
    print("[POSTMSG] enviado. Olha o jogo.")

def send_input():
    """SendInput simula clique de hardware -- mais autentico."""
    print("\n[INPUT] Modo hardware -- vou MOVER seu cursor e clicar.")
    print("        TIRA A MAO DO MOUSE agora. Comeca em 3s...")
    time.sleep(3)

    pt = wintypes.POINT(CLICK_X, CLICK_Y)
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))
    screen_x, screen_y = pt.x, pt.y
    print(f"  client ({CLICK_X},{CLICK_Y}) -> screen ({screen_x},{screen_y})")

    print("  Focando janela do TO...")
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"  AVISO: SetForegroundWindow falhou: {e}")
    time.sleep(0.5)

    print(f"  Movendo cursor pra ({screen_x},{screen_y})...")
    win32api.SetCursorPos((screen_x, screen_y))
    time.sleep(0.5)

    actual = win32api.GetCursorPos()
    print(f"  Cursor agora em: {actual}")
    if actual != (screen_x, screen_y):
        print(f"  AVISO: cursor NAO foi pro lugar esperado! Pode haver bloqueio de SetCursorPos.")

    print("  Clicando (mouse_event LBUTTON down + up)...")
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.5)
    print("[INPUT] enviado. Olha o jogo nos proximos 3 segundos.")
    time.sleep(3)
    print("[INPUT] fim. O surroundings abriu?")

if method in ('SENDMSG', 'ALL'):
    sendmsg()
    if method == 'ALL':
        time.sleep(3)
        print("\n--- aguarda 3s, fechando surroundings (se abriu, aperta ESC no jogo) ---")
        time.sleep(2)

if method in ('POSTMSG', 'ALL'):
    postmsg()
    if method == 'ALL':
        time.sleep(3)
        print("\n--- aguarda 3s ---")
        time.sleep(2)

if method in ('INPUT', 'ALL'):
    send_input()

print("\nFim do teste.")
