"""
Teste isolado: abre o painel Surroundings via open_surroundings_ui()
da AbstractClientWindow -- so isso, nada de bot, nada de sell, nada de loop.

Usa a formula nova: pos = (window_width - 49, 60)
"""
import time
import pymem
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

# Acha o processo do TO
proc = None
for p in PymemProcess.list_clients():
    proc = p
    break
if proc is None:
    raise SystemExit("client.exe nao encontrado")

print(f"Process: PID={proc.process_id}")

# Cria a janela (mesmo objeto que o bot usa)
client = Win32ClientWindow(proc)

ww, wh = client.get_window_size()
print(f"Window size: {ww} x {wh}")
print(f"open_surroundings_ui vai clicar em: ({ww - 49}, 60)")
print()
print("Vai clicar em 3 segundos... olha o jogo")
time.sleep(3)

print("Clicando agora!")
client.open_surroundings_ui()

print()
print("Done. O painel Surroundings abriu?")
