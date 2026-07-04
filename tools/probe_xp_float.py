"""
Search for the XP% FLOAT in the char struct: take a snapshot of all floats,
wait 12s (KILL MOBS), and show the floats that INCREASED and are in 0-100
(candidates for XP% like 64.5895).
"""
import time

from GhostBot.lib.tooling import get_client, snapshot_float_offsets

client = get_client()
p = client.pointers
pm = p.pm
base_ptr = p.CLIENT + 0x00D450EC
offsets = list(range(0, 0x2000, 4))

print("Initial snapshot. KILL MOBS for 12s!")
first = snapshot_float_offsets(pm, base_ptr, offsets)
time.sleep(12)
last = snapshot_float_offsets(pm, base_ptr, offsets)
print("\n=== Floats that INCREASED and are in 0-100 (XP% candidates) ===")
hits = 0
for off in offsets:
    f0, f1 = first[off], last[off]
    if f0 is None or f1 is None:
        continue
    if f1 > f0 and 0 < f1 < 100 and (f1 - f0) < 8:
        print(f"  +{off:#06x}  {f0:.4f} -> {f1:.4f}  (delta {f1 - f0:.4f})")
        hits += 1
if not hits:
    print("  (none) -- the % may be calculated by the game, not stored as a float.")
