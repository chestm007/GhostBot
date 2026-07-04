from __future__ import annotations

from dataclasses import dataclass
from ctypes import wintypes
import ctypes

import win32api

from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.tooling import get_client


@dataclass(frozen=True)
class MapOffsetCapture:
    title: tuple[int, int]
    offset: tuple[int, int]


def capture_map_offset(title_bmp: str, threshold: float = 0.70, client: Win32ClientWindow | None = None) -> MapOffsetCapture | None:
    """Capture the cursor offset from a visible map/dialog title template.

    Returns the title center and cursor-relative offset, or None if the title cannot be found.
    """
    client = client or get_client()
    title = client._image_finder.find_button_center(title_bmp, threshold=threshold)
    if title is None:
        return None

    sx, sy = win32api.GetCursorPos()
    pt = wintypes.POINT(sx, sy)
    ctypes.windll.user32.ScreenToClient(client.window_handle, ctypes.byref(pt))
    return MapOffsetCapture(title=title, offset=(pt.x - title[0], pt.y - title[1]))
