"""
Read target_hp / energy / level live for 20s, to diagnose the dashboard.
Hit a mob during the test to see if target_hp changes.
"""
import math
import time

from GhostBot.lib.tooling import get_client

TARGET_MAX_HP, TARGET_MIN_HP = 597, 461

client = get_client()
p = client.pointers
print("Reading for 20s (aim and hit a mob now)...")
for _ in range(20):
    def safe(fn):
        try:
            return fn()
        except Exception as e:
            return f"ERRO {type(e).__name__}"
    sel = safe(p.is_target_selected)   # property gate
    raw = safe(p.target_hp)            # raw value from pointer
    # replicate the target_hp property of client_window:
    if sel is True:
        prop = (math.ceil((raw - TARGET_MIN_HP) / (TARGET_MAX_HP - TARGET_MIN_HP) * 100)
                if isinstance(raw, int) and raw >= TARGET_MIN_HP else -1)
    else:
        prop = None
    en = safe(p.get_energy)
    print(f"  selected={sel!r:>6}  raw={raw!r:>6}  PROPERTY(0-100)={prop!r:>6}  energy={en!r}")
    time.sleep(1)
