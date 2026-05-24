"""
Detecta onde seu mouse esta na janela do TO.
Voce posiciona o mouse fisico em cima do botao do olho (sem clicar),
volta no terminal e aperta Enter. O script mostra a coord screen E client.
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

print("=" * 60)
print("  POSICIONA SEU MOUSE em cima do botao do olho (Surroundings)")
print("  no jogo. NAO CLICA. Depois volta aqui e aperta ENTER.")
print("=" * 60)
input("\nPosicionou? Aperta ENTER pra ler a coord do cursor...")

# Le posicao na tela
screen_x, screen_y = win32api.GetCursorPos()

# Converte pra client coord
pt = wintypes.POINT(screen_x, screen_y)
ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(pt))
client_x, client_y = pt.x, pt.y

print(f"\nCursor agora:")
print(f"  Screen coord: ({screen_x}, {screen_y})")
print(f"  Client coord (relativa a janela do TO): ({client_x}, {client_y})")

# Compara com o que template matching achou
print(f"\nTemplate matching achou em: (1549, 90) client coord")
diff_x = client_x - 1549
diff_y = client_y - 90
print(f"Diferenca: ({diff_x:+d}, {diff_y:+d}) pixels")

if abs(diff_x) <= 15 and abs(diff_y) <= 15:
    print("  -> COORD BATE. Template matching ta correto.")
    print("  -> Problema eh injection de click (SendMessage nao funciona pra esse botao).")
else:
    print("  -> COORD DIFERE muito. Template matching ta achando lugar errado.")
    print("  -> Provavel false positive do template ou janela mudou de tamanho.")
