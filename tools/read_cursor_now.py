"""Read the cursor position immediately in client coordinates."""
from __future__ import annotations

import win32api

from _shared import get_client, screen_to_client


client = get_client()
ww, wh = client.get_window_size()
sx, sy = win32api.GetCursorPos()
cx, cy = screen_to_client(client.window_handle, (sx, sy))

print(f"Window: {ww} x {wh}")
print(f"Cursor: screen ({sx}, {sy}) | client ({cx}, {cy})")
print()
print(f"Offset top-left:     ({cx}, {cy})")
print(f"Offset top-right:    ({ww - cx}, {cy})")
print(f"Offset bottom-left:  ({cx}, {wh - cy})")
print(f"Offset bottom-right: ({ww - cx}, {wh - cy})")
print(f"Offset CENTER:       ({cx - ww // 2:+d}, {cy - wh // 2:+d})  <-- for centered elements (char, etc)")
