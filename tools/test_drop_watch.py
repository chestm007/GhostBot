"""
Live test of Step 1: read the System chat in a loop and log detected drops
(with the category from alertas_drop.txt). No Discord yet.

Usage:
    python tools/test_drop_watch.py [interval_sec] [duration_sec]

  - interval: how often to read the chat (default 2s).
  - duration: how long to run in total (default 60s).
               Pass 0 for a SINGLE SHOT (smoke test: log what's currently
               visible and exit).
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

WATCHLIST = r"C:\Bot\BotTO\alertas_drop.txt"

interval = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
duration = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0

client = get_client()
watcher = DropWatcher(WATCHLIST)

ICON = {"want": "[QUERO]  ", "ignore": "[ignora] ", "unknown": "[NOVO?]  "}

print(f"QUERO   = {sorted(watcher.want)}")
print(f"NAO QUERO = {sorted(watcher.ignore)}")

if duration <= 0:
    # single shot: no priming, show what's currently visible in chat
    print("\n-- single shot (what's visible in chat now) --")
    alerts, _ = watcher.poll(client)
    if not alerts:
        print("(nothing detected -- was the anchor found? is there a visible drop line?)")
    for name, cat in alerts:
        print(f"  {ICON.get(cat, cat)} {name}")
    raise SystemExit(0)

# loop: PRIME the dedup (mark what's already on screen as seen),
# to only show NEW drops from here on.
watcher.prime(client)
print(f"\nPrimed. Reading every {interval}s for {duration:.0f}s.")
print(">>> Go to the game and drop something -- it should appear below:\n")

end = time.time() + duration
while time.time() < end:
    alerts, _ = watcher.poll(client)
    for name, cat in alerts:
        ts = time.strftime("%H:%M:%S")
        print(f"{ts} {ICON.get(cat, cat)} {name}", flush=True)
    time.sleep(interval)

print("\n-- end of test --")
