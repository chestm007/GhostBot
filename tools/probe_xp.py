"""
Probe neighboring offsets of the char struct (client.exe+0x00D450EC) to find XP.
Take a snapshot, wait 15s (KILL MOBS!), take another, and show what changed.
XP = offset that ONLY INCREASES (and whose float matches the % on screen).
"""
import time

from GhostBot.lib.tooling import get_client, snapshot_int_float_offsets

client = get_client()
p = client.pointers
pm = p.pm
base_ptr = p.CLIENT + 0x00D450EC
known = {0xDC: 'MAX_HP', 0x3B8: 'HP', 0x3BC: 'MANA', 0x3C4: 'LEVEL', 0x3CC: 'ENERGY', 0x410: 'GOLD'}
offsets = list(range(0x300, 0x460, 4))

print("Initial snapshot taken. KILL MOBS now for 15s to gain XP!")
first = snapshot_int_float_offsets(pm, base_ptr, offsets)
time.sleep(15)
last = snapshot_int_float_offsets(pm, base_ptr, offsets)

print("\n=== Offsets that INCREASED (XP candidates) ===")
for off in offsets:
    i0, f0 = first[off]
    i1, f1 = last[off]
    if i0 is None or i1 is None or f0 is None or f1 is None:
        continue
    if i1 > i0:  # only increased
        tag = known.get(off, '?')
        fflag = ' <== float parece % (0-100)' if (0 < f1 < 100) else ''
        print(f"  +{off:#05x} [{tag:6}] int {i0} -> {i1} (delta {i1 - i0}) | float {f0:.4f} -> {f1:.4f}{fflag}")

print("\n=== Others that changed (went up and down, e.g. HP/Mana) ===")
for off in offsets:
    i0, f0 = first[off]
    i1, f1 = last[off]
    if i0 is None or i1 is None or i1 == i0 or i1 > i0:
        continue
    tag = known.get(off, '?')
    print(f"  +{off:#05x} [{tag:6}] int {i0} -> {i1}")
