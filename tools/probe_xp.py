"""
Sonda offsets vizinhos da char struct (client.exe+0x00D450EC) pra achar o XP.
Tira um snapshot, espera 15s (MATE MOBS!), tira outro, e mostra o que mudou.
XP = offset que SO AUMENTA (e cujo float bate com a % da tela).
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
known = {0xDC: 'MAX_HP', 0x3B8: 'HP', 0x3BC: 'MANA', 0x3C4: 'LEVEL', 0x3CC: 'ENERGY', 0x410: 'GOLD'}
offsets = list(range(0x300, 0x460, 4))


def snap():
    sb = pm.read_int(base_ptr)
    d = {}
    for off in offsets:
        try:
            d[off] = (pm.read_int(sb + off), pm.read_float(sb + off))
        except Exception:
            d[off] = (None, None)
    return d


print("Snapshot inicial tirado. MATE MOBS agora por 15s pra ganhar XP!")
first = snap()
time.sleep(15)
last = snap()

print("\n=== Offsets que AUMENTARAM (candidatos a XP) ===")
for off in offsets:
    i0, f0 = first[off]
    i1, f1 = last[off]
    if i0 is None or i1 is None:
        continue
    if i1 > i0:  # so aumentou
        tag = known.get(off, '?')
        fflag = ' <== float parece % (0-100)' if (0 < f1 < 100) else ''
        print(f"  +{off:#05x} [{tag:6}] int {i0} -> {i1} (delta {i1 - i0}) | float {f0:.4f} -> {f1:.4f}{fflag}")

print("\n=== Outros que mudaram (subiu E desceu, ex HP/Mana) ===")
for off in offsets:
    i0, f0 = first[off]
    i1, f1 = last[off]
    if i0 is None or i1 is None or i1 == i0 or i1 > i0:
        continue
    tag = known.get(off, '?')
    print(f"  +{off:#05x} [{tag:6}] int {i0} -> {i1}")
