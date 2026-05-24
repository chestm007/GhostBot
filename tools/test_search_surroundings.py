"""
Teste isolado: abre o painel Surroundings + clica no botao Search + digita 'Blacksmith'.

Voce deve manter o painel Surroundings no canto SUPERIOR ESQUERDO da janela do TO.
"""
import time
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

proc = next(iter(PymemProcess.list_clients()), None)
if proc is None:
    raise SystemExit("client.exe nao encontrado")

print(f"PID={proc.process_id}")
client = Win32ClientWindow(proc)

ww, wh = client.get_window_size()
print(f"Window: {ww} x {wh}")
print()
print("Vai abrir surroundings + clicar search + digitar 'Blacksmith' em 3s...")
print("LEMBRA: painel Surroundings precisa estar no canto SUPERIOR ESQUERDO.")
time.sleep(3)

client.search_surroundings("Blacksmith")
print()
print("Done. Verifica no jogo: o painel abriu, clicou no Search, e digitou Blacksmith?")
