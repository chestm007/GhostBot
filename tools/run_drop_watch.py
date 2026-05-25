"""
Monitor de drops ao vivo -> Discord.

Le o chat System em loop, e quando cai um item da lista QUERO (ou um item
NOVO, fora das duas listas), posta no Discord via webhook. Itens da lista
NAO QUERO sao ignorados.

Uso:
    python tools/run_drop_watch.py [intervalo_seg] [duracao_seg]

  - intervalo: de quanto em quanto tempo le o chat (padrao 2s).
  - duracao:   por quanto tempo roda (padrao 0 = pra sempre; Ctrl+C pra parar).

Pre-requisitos: jogo aberto, aba System selecionada no chat, e a URL do
webhook em discord_webhook.txt.
"""
import os
import sys
import time

sys.path.insert(0, r"C:\Bot\BotTO\src")

from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.drop_watcher import DropWatcher
from GhostBot.discord_notify import send, send_drop_alert

WATCHLIST = r"C:\Bot\BotTO\alertas_drop.txt"

interval = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
duration = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0  # 0 = pra sempre

proc = next(iter(PymemProcess.list_clients()), None)
if proc is None:
    raise SystemExit("client.exe nao encontrado -- o jogo esta aberto?")
client = Win32ClientWindow(proc)

try:
    char = client.pointers.get_char_name()
except Exception:
    char = None

watcher = DropWatcher(WATCHLIST)
ICON = {"want": "[QUERO]  ", "ignore": "[ignora] ", "unknown": "[NOVO?]  "}

print(f"Char: {char}")
print(f"QUERO   = {sorted(watcher.want)}")
print(f"NAO QUERO = {sorted(watcher.ignore)}")
print(f"Lendo a cada {interval}s. {'Ctrl+C pra parar.' if duration <= 0 else f'Por {duration:.0f}s.'}\n")

# ping de inicio, pra confirmar que esta no ar
send(f"👀 Monitorando drops{(' — **' + char + '**') if char else ''}")

# prima o dedup (marca o que ja esta na tela como visto) -> so alerta drops novos
watcher.prime(client)

end = time.time() + duration if duration > 0 else None
try:
    while end is None or time.time() < end:
        for name, cat in watcher.poll(client):
            ts = time.strftime("%H:%M:%S")
            print(f"{ts} {ICON.get(cat, cat)} {name}", flush=True)
            if cat == "ignore":
                continue  # nao alerta lixo
            send_drop_alert(name, cat, char)
        time.sleep(interval)
except KeyboardInterrupt:
    print("\nparado.")

print("\n-- fim --")
