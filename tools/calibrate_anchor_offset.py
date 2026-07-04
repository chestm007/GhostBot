"""Calibrate an anchored offset by matching a BMP and reading the cursor at the same instant."""
from __future__ import annotations

import sys

from _shared import get_client, match_template, screen_to_client


DEFAULT_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\npc_dialogue_title.bmp"
THRESHOLD = 0.70


def main() -> None:
    bmp_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BMP

    client = get_client()
    hwnd = client.window_handle
    ww, wh = client.get_window_size()

    match = match_template(client, bmp_path, threshold=THRESHOLD)
    cx, cy = screen_to_client(hwnd)

    name = bmp_path.replace("\\", "/").split("/")[-1]
    print(f"Anchor '{name}': center=({match.center[0]},{match.center[1]})  score={match.score:.3f}  "
          f"{'OK' if match.score >= THRESHOLD else '<<< BELOW THRESHOLD!'}")
    print(f"Window: {ww} x {wh}")
    print(f"Cursor: client=({cx},{cy})")
    print(f">>> OFFSET (cursor - anchor) = ({cx - match.center[0]}, {cy - match.center[1]})")


if __name__ == "__main__":
    main()
