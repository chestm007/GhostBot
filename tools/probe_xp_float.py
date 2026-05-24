"""
Procura o FLOAT do XP% na char struct: tira snapshot de todos os floats,
espera 12s (MATE MOBS), e mostra os floats que AUMENTARAM e estao em 0-100
(candidatos ao XP% tipo 64.5895).
"""
import time
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.lib.talisman_online_python.pointers import Pointers

proc = next(iter(PymemProcess.list_clients()), None)
if proc is None:
    raise SystemExit("client.exe nao encontrado")
p = Pointers(proc.process_id)
pm = p.pm
base_ptr = p.CLIENT + 0x00D450EC
offsets = list(range(0, 0x2000, 4))


def snap():
    sb = pm.read_int(base_ptr)
    d = {}
    for off in offsets:
        try:
            d[off] = pm.read_float(sb + off)
        except Exception:
            d[off] = None
    return d


print("Snapshot inicial. MATE MOBS por 12s!")
first = snap()
time.sleep(12)
last = snap()
print("\n=== Floats que AUMENTARAM e estao em 0-100 (candidatos a XP%) ===")
hits = 0
for off in offsets:
    f0, f1 = first[off], last[off]
    if f0 is None or f1 is None:
        continue
    if f1 > f0 and 0 < f1 < 100 and (f1 - f0) < 8:
        print(f"  +{off:#06x}  {f0:.4f} -> {f1:.4f}  (delta {f1 - f0:.4f})")
        hits += 1
if not hits:
    print("  (nenhum) -- a % pode ser calculada pelo jogo, nao guardada como float.")
