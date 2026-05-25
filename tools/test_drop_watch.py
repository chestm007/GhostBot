"""
Teste ao vivo da Etapa 1: le o chat System em loop e loga os drops detectados
(com a categoria do alertas_drop.txt). SEM Discord ainda.

Uso:
    python tools/test_drop_watch.py [intervalo_seg] [duracao_seg]

  - intervalo: de quanto em quanto tempo le o chat (padrao 2s).
  - duracao:   por quanto tempo roda no total (padrao 60s).
               Passe 0 pra um TIRO UNICO (smoke test: loga o que estiver
               visivel agora e sai).
"""
import os
import sys
import time

sys.path.insert(0, r"C:\Bot\BotTO\src")

from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.drop_watcher import DropWatcher

WATCHLIST = r"C:\Bot\BotTO\alertas_drop.txt"

interval = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
duration = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0

proc = next(iter(PymemProcess.list_clients()), None)
if proc is None:
    raise SystemExit("client.exe nao encontrado -- o jogo esta aberto?")
client = Win32ClientWindow(proc)
watcher = DropWatcher(WATCHLIST)

ICON = {"want": "[QUERO]  ", "ignore": "[ignora] ", "unknown": "[NOVO?]  "}

print(f"QUERO   = {sorted(watcher.want)}")
print(f"NAO QUERO = {sorted(watcher.ignore)}")

if duration <= 0:
    # tiro unico: sem priming, mostra o que estiver visivel agora
    print("\n-- tiro unico (o que esta visivel no chat agora) --")
    hits = watcher.poll(client)
    if not hits:
        print("(nada detectado -- a ancora foi achada? tem linha de drop visivel?)")
    for name, cat in hits:
        print(f"  {ICON.get(cat, cat)} {name}")
    raise SystemExit(0)

# loop: primeiro poll so PRIMA o dedup (descarta o que ja estava na tela),
# pra so mostrar drops NOVOS dali pra frente.
watcher.poll(client)
print(f"\nPrimado. Lendo a cada {interval}s por {duration:.0f}s.")
print(">>> Vai no jogo e dropa algo -- deve aparecer aqui embaixo:\n")

end = time.time() + duration
while time.time() < end:
    for name, cat in watcher.poll(client):
        ts = time.strftime("%H:%M:%S")
        print(f"{ts} {ICON.get(cat, cat)} {name}", flush=True)
    time.sleep(interval)

print("\n-- fim do teste --")
