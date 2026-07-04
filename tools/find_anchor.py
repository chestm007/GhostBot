"""Discovery tool for TO UI anchors."""
from __future__ import annotations

from _shared import describe_offset, get_client, screen_to_client


client = get_client()
ww, wh = client.get_window_size()

print("=" * 60)
print(f"  TO window: {ww} x {wh}")
print("=" * 60)
print()
print("  POSITION YOUR MOUSE over the element you want (without clicking),")
print("  then come back here and press ENTER.")
input("\nReady? Reading now: ")

# Read position on screen and convert to client
cx, cy = screen_to_client(client.window_handle)

print()
print(f"Cursor: client ({cx}, {cy})")
print(f"Window: {ww} x {wh}")
print()
print("Offset from each corner:")
offsets = describe_offset(cx, cy, ww, wh)
for corner, (ox, oy) in offsets.items():
    print(f"  {corner:13s}: ({ox:+5d}, {oy:+5d})  -- distance: {abs(ox) + abs(oy)}")

# Suggest anchor: the corner with the smallest sum of absolute offsets
best_corner = min(offsets.items(), key=lambda kv: abs(kv[1][0]) + abs(kv[1][1]))
corner, best_offset = best_corner
print()
print(f">>> LIKELY ANCHOR: {corner} with offset {best_offset}")
print()
print("Suggested formula for the code:")
ox, oy = best_offset
if corner == 'top-left':
    print(f"  pos = ({ox}, {oy})")
elif corner == 'top-right':
    print(f"  pos = (window_width - {ox}, {oy})")
elif corner == 'bottom-left':
    print(f"  pos = ({ox}, window_height - {oy})")
elif corner == 'bottom-right':
    print(f"  pos = (window_width - {ox}, window_height - {oy})")
