from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import win32api

from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess


@dataclass(frozen=True)
class TemplateMatch:
    top_left: tuple[int, int]
    center: tuple[int, int]
    score: float
    size: tuple[int, int]


def get_client() -> Win32ClientWindow:
    proc = next(iter(PymemProcess.list_clients()), None)
    if proc is None:
        raise SystemExit("client.exe not found")
    return Win32ClientWindow(proc)


def load_gray_template(bmp_path: str | Path):
    bmp = cv2.imread(str(bmp_path), cv2.IMREAD_GRAYSCALE)
    if bmp is None:
        raise SystemExit(f"BMP not found: {bmp_path}")
    return bmp


def match_template(client: Win32ClientWindow, bmp_path: str | Path, threshold: float = 0.7) -> TemplateMatch:
    win = client.capture_window()
    bmp = load_gray_template(bmp_path)
    res = cv2.matchTemplate(win, bmp, cv2.TM_CCOEFF_NORMED)
    _, score, _, top_left = cv2.minMaxLoc(res)
    if score < threshold:
        raise SystemExit(f"template score below threshold: {score:.3f} < {threshold:.3f}")
    h, w = bmp.shape[:2]
    x, y = top_left
    return TemplateMatch(top_left=(x, y), center=(x + w // 2, y + h // 2), score=score, size=(w, h))


def find_template_center(client: Win32ClientWindow, bmp_path: str | Path, threshold: float = 0.7) -> tuple[tuple[int, int], float]:
    match = match_template(client, bmp_path, threshold=threshold)
    return match.center, match.score


def screen_to_client(hwnd, screen_pos: tuple[int, int] | None = None) -> tuple[int, int]:
    sx, sy = screen_pos or win32api.GetCursorPos()
    pt = wintypes.POINT(sx, sy)
    ctypes.windll.user32.ScreenToClient(int(hwnd), ctypes.byref(pt))
    return pt.x, pt.y


def snapshot_int_float_offsets(pm, base_ptr: int, offsets: Iterable[int]) -> dict[int, tuple[int | None, float | None]]:
    sb = pm.read_int(base_ptr)
    data: dict[int, tuple[int | None, float | None]] = {}
    for off in offsets:
        try:
            data[off] = (pm.read_int(sb + off), pm.read_float(sb + off))
        except Exception:
            data[off] = (None, None)
    return data


def snapshot_float_offsets(pm, base_ptr: int, offsets: Iterable[int]) -> dict[int, float | None]:
    sb = pm.read_int(base_ptr)
    data: dict[int, float | None] = {}
    for off in offsets:
        try:
            data[off] = pm.read_float(sb + off)
        except Exception:
            data[off] = None
    return data
