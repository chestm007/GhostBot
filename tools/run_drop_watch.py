"""
Live drop monitor -> Discord.

Reads the System chat in a loop, and when an item from the WANT list drops (or a
NEW item, outside both lists), posts to Discord via webhook. Items from the
DON'T WANT list are ignored.

Usage:
    python tools/run_drop_watch.py [interval_sec] [duration_sec]

  - interval: how often to read the chat (default 2s).
  - duration: how long to run (default 0 = forever; Ctrl+C to stop).

Prerequisites: game open, System tab selected in chat, and the webhook URL in
discord_webhook.txt.
"""
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from GhostBot.lib.tooling import get_client
from GhostBot.drop_watcher import DropWatcher
from GhostBot.discord_notify import send, send_drop_alert

WATCHLIST = r"C:\Bot\BotTO\alertas_drop.txt"

interval = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
duration = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0  # 0 = pra sempre

client = get_client()

try:
    char = client.pointers.get_char_name()
except Exception:
    char = None

watcher = DropWatcher(WATCHLIST)
ICON = {"want": "[QUERO]  ", "ignore": "[ignora] ", "unknown": "[NOVO?]  "}

print(f"Char: {char}")
print(f"QUERO   = {sorted(watcher.want)}")
print(f"NAO QUERO = {sorted(watcher.ignore)}")
print(f"Reading every {interval}s. {'Ctrl+C to stop.' if duration <= 0 else f'For {duration:.0f}s.'}\n")

# start ping, to confirm it's up
send(f"👀 Monitorando drops{(' — **' + char + '**') if char else ''}")

# prime the dedup (mark what's already on screen as seen) -> only alert new drops
watcher.prime(client)

end = time.time() + duration if duration > 0 else None
try:
    while end is None or time.time() < end:
        alerts, _deltas = watcher.poll(client)
        for name, cat in alerts:
            ts = time.strftime("%H:%M:%S")
            print(f"{ts} {ICON.get(cat, cat)} {name}", flush=True)
            if cat == "ignore":
                continue  # don't alert junk
            send_drop_alert(name, cat, char)
        time.sleep(interval)
except KeyboardInterrupt:
    print("\nstopped.")

print("\n-- end --")
