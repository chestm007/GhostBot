"""
Le target_hp / energy / level ao vivo por 20s, pra diagnosticar o dashboard.
Bata num mob durante o teste pra ver se target_hp muda.
"""
import time
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.lib.talisman_online_python.pointers import Pointers

proc = next(iter(PymemProcess.list_clients()), None)
if proc is None:
    raise SystemExit("client.exe nao encontrado")
import math
TARGET_MAX_HP, TARGET_MIN_HP = 597, 461
p = Pointers(proc.process_id)
print("Lendo por 20s (mira e bata num mob agora)...")
for _ in range(20):
    def safe(fn):
        try:
            return fn()
        except Exception as e:
            return f"ERRO {type(e).__name__}"
    sel = safe(p.is_target_selected)   # gate da property
    raw = safe(p.target_hp)            # valor cru do pointer
    # replica a property target_hp de client_window:
    if sel is True:
        prop = (math.ceil((raw - TARGET_MIN_HP) / (TARGET_MAX_HP - TARGET_MIN_HP) * 100)
                if isinstance(raw, int) and raw >= TARGET_MIN_HP else -1)
    else:
        prop = None
    en = safe(p.get_energy)
    print(f"  selected={sel!r:>6}  raw={raw!r:>6}  PROPERTY(0-100)={prop!r:>6}  energy={en!r}")
    time.sleep(1)
