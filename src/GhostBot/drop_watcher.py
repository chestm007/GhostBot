"""
Drop detection via TO System chat OCR (Tesseract).

Flow:
  capture the window -> find the ANCHOR (3 chat icons) -> crop the read region
  (calibrated offsets) -> preprocess image (grayscale+zoom+Otsu) -> OCR
  -> extract item names from "You got the item: [Name(lvl X)]" lines.

Initial calibration (2026-05-25, owner's window): anchor 64x24; region relative
to anchor's top-left. Each player can recalibrate with
`tools/calibrate_chat_region.py` (offsets become per-player config in UI
later on).
"""
from __future__ import annotations

import difflib
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
import pytesseract

from GhostBot import logger
from GhostBot.lib.text_utils import clean_item_name

# pytesseract logs the full command line on every call (INFO) -> spam.
# Since we read the chat every few seconds, this floods the log. Silence it.
logging.getLogger("pytesseract").setLevel(logging.WARNING)

if TYPE_CHECKING:
    from GhostBot.abstract_client_window import AbstractClientWindow

_path_base = os.path.dirname(__file__)


# ----------------------------------------------------------------------------
# Tesseract: not on PATH by default. Look for the installed .exe, and also
# a bundled copy in the package (for the future .exe we distribute to friends).
# ----------------------------------------------------------------------------
def _find_tesseract() -> str | None:
    # Folders where the PORTABLE copy may be (running from source OR compiled):
    #  - _path_base = dir of the GhostBot package. In source it's src/GhostBot; in nuitka
    #    the included data-dir as GhostBot/Tesseract-OCR ends up here (__file__ resolves).
    #  - .exe directory (standalone/dist .exe: the folder sits alongside / in GhostBot/).
    bases = [_path_base]
    try:
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        bases += [exe_dir, os.path.join(exe_dir, "GhostBot")]
    except Exception:
        pass
    candidates = [os.path.join(b, "Tesseract-OCR", "tesseract.exe") for b in bases]
    candidates += [  # fallback: instalacao do sistema
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    return next((c for c in candidates if os.path.exists(c)), None)


_TESS = _find_tesseract()
if _TESS:
    pytesseract.pytesseract.tesseract_cmd = _TESS
else:
    logger.warning("drop_watcher :: Tesseract not found -- drop OCR will fail")


def tesseract_available() -> bool:
    return _TESS is not None

_TESS_CONFIG = "--psm 6"  # uniform text block (multiple chat lines)

# ----------------------------------------------------------------------------
# Read region: offsets relative to the TOP-LEFT of the anchor (calibrated).
# (left, top, right, bottom) -> x in [ax+left, ax+right], y in [ay+top, ay+bottom]
# ----------------------------------------------------------------------------
ANCHOR_BMP = os.path.join(_path_base, "Images", "misc", "chat_anchor.bmp")
ANCHOR_THRESHOLD = 0.80
OCR_REGION_OFFSETS = (0, -158, 378, 0)

# ----------------------------------------------------------------------------
# Item name extraction from chat lines
# ----------------------------------------------------------------------------
# Ideal case: "got the item: [Name]" / "[Name(lvl X)]"
_ITEM_RE = re.compile(r"got the item:\s*[\[\(]\s*(.+?)\s*[\]\)]", re.IGNORECASE)
# Fallback: OCR mangles the "got the item" prefix but reads "[name]" correctly.
# Tolerates [<->( and ]<->), and skips an optional "(lvl N)" before closing.
_BRACKET_RE = re.compile(
    r"[\[\(]\s*([A-Za-z][A-Za-z '\-]{3,40}?)\s*(?:\(lvl\s*\d+\))?\s*[\]\)]"
)

MIN_NAME_LEN = 4  # real item names are >= 4 letters; cuts fragments ('XY', 'Red')


def _looks_like_item(name: str) -> bool:
    return len(name) >= MIN_NAME_LEN


def extract_item_names(text: str) -> list[str]:
    """Extract item names from drop lines in text read by OCR.

    Lines like "Congratulations! [Player]" also have brackets but are NOT
    items -- they are ignored. Short OCR noise fragments are discarded.
    """
    names: list[str] = []
    for line in text.splitlines():
        if (m := _ITEM_RE.search(line)):
            if _looks_like_item(name := clean_item_name(m.group(1))):
                names.append(name)
            continue
        if "congrat" in line.lower():
            continue
        for raw in _BRACKET_RE.findall(line):
            if _looks_like_item(name := clean_item_name(raw)):
                names.append(name)
    return names


# ----------------------------------------------------------------------------
# "Inventory full" detection -- SAME chat region (same OCR read).
# Game text: "Your item box is full." OCR mangles letters, so normalize
# to letters-only and match the distinctive core ('item box is full').
# ----------------------------------------------------------------------------
_BOX_FULL_CORE = "itemboxisfull"
# OCR swaps letter<->digit (o->0, l->1, e->3...). Undo common swaps
# BEFORE comparing, otherwise 'Y0ur 1tem b0x is fu11' won't match 'item box is full'.
_OCR_DIGIT_FIX = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s", "8": "b", "!": "l", "|": "l"})
_BOX_FULL_SIM = 0.72  # similarity threshold (distinctive core -> safe against false positive)


def chat_says_box_full(text: str) -> bool:
    """True if any chat line looks like 'Your item box is full.'
    (core 'itemboxisfull' as substring OR similarity >= threshold; tolerates OCR noise)."""
    for line in text.splitlines():
        norm = re.sub(r"[^a-z]", "", line.lower().translate(_OCR_DIGIT_FIX))
        if len(norm) < 8:
            continue
        if _BOX_FULL_CORE in norm:
            return True
        if difflib.SequenceMatcher(None, norm, _BOX_FULL_CORE).ratio() >= _BOX_FULL_SIM:
            return True
    return False


def _preprocess(bgr):
    """Treatment B (winner in tests): grayscale + 4x zoom + Otsu."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    big = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    _, thr = cv2.threshold(big, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if np.mean(thr) < 127:  # light text on dark background -> invert
        thr = cv2.bitwise_not(thr)
    return thr


def find_anchor_top_left(client: "AbstractClientWindow") -> tuple[int, int] | None:
    """Top-left of the anchor (3 chat icons) in the window. None if not found
    (chat closed, different tab, window covered...)."""
    tmpl = cv2.imread(ANCHOR_BMP, cv2.IMREAD_GRAYSCALE)
    if tmpl is None:
        logger.error("drop_watcher :: anchor bmp not found: %s", ANCHOR_BMP)
        return None
    win = client.capture_window()  # grayscale, como o resto do bot
    res = cv2.matchTemplate(win, tmpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, (x, y) = cv2.minMaxLoc(res)
    if score < ANCHOR_THRESHOLD:
        logger.debug("drop_watcher :: anchor score low %.3f (<%.2f)", score, ANCHOR_THRESHOLD)
        return None
    return x, y


def read_chat_text(client: "AbstractClientWindow") -> str | None:
    """Read the chat region and return the RAW OCR text.
    None = anchor not found (can't read now); "" = empty region.
    Common base: 1 read works for both drops and 'inventory full'."""
    anchor = find_anchor_top_left(client)
    if anchor is None:
        return None
    ax, ay = anchor
    lo, to, ro, bo = OCR_REGION_OFFSETS
    color = client.capture_window(color=True)
    h, w = color.shape[:2]
    x1, y1 = max(0, ax + lo), max(0, ay + to)
    x2, y2 = min(w, ax + ro), min(h, ay + bo)
    if not (x2 > x1 and y2 > y1):
        return ""
    crop = color[y1:y2, x1:x2]
    return pytesseract.image_to_string(_preprocess(crop), config=_TESS_CONFIG)


def read_chat_items(client: "AbstractClientWindow") -> list[str] | None:
    """Item names detected in chat. None = anchor not found."""
    text = read_chat_text(client)
    if text is None:
        return None
    return extract_item_names(text)


# ----------------------------------------------------------------------------
# Watchlist (alertas_drop.txt)
# ----------------------------------------------------------------------------
def _watchlist_candidates() -> list[str]:
    """Folders where alertas_drop.txt may be (source AND compiled .exe)."""
    bases = [
        os.path.join(os.path.expanduser("~"), "GhostBot"),        # per-player config
        os.path.normpath(os.path.join(_path_base, "..", "..")),   # repo root (source)
        _path_base,
    ]
    try:  # .exe folder (and /GhostBot) -- where the friends' package puts the file
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        bases += [exe_dir, os.path.join(exe_dir, "GhostBot")]
    except Exception:
        pass
    return [os.path.join(b, "alertas_drop.txt") for b in bases]


_WATCHLIST_CANDIDATES = _watchlist_candidates()


def default_watchlist_path() -> str:
    """Find alertas_drop.txt (HOME/GhostBot, then repo root/.exe)."""
    for p in _WATCHLIST_CANDIDATES:
        if os.path.exists(p):
            return p
    return _WATCHLIST_CANDIDATES[0]  # default: HOME/GhostBot (created by whoever uses it)


def load_watchlist(path) -> tuple[set[str], set[str]]:
    """Read alertas_drop.txt -> (want, not_want) in lowercase."""
    want: set[str] = set()
    ignore: set[str] = set()
    target: set[str] | None = None
    try:
        for raw in Path(path).read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            up = line.upper()
            if up.startswith("[WANT"):
                target = want
                continue
            if up.startswith("[DON'T WANT") or up.startswith("[DON'T WANT"):
                target = ignore
                continue
            if target is not None:
                target.add(line.lower())
    except FileNotFoundError:
        logger.warning("drop_watcher :: watchlist not found: %s", path)
    return want, ignore


def classify(name: str, want: set[str], ignore: set[str]) -> str:
    """'want' | 'ignore' | 'unknown'."""
    n = name.lower()
    if n in want:
        return "want"
    if n in ignore:
        return "ignore"
    return "unknown"


def add_to_watchlist(name: str, which: str, path=None) -> None:
    """Add `name` to the 'want' (WANT) or 'ignore' (DON'T WANT) section of
    alertas_drop.txt, removing it from wherever it was before (no duplicates). UI and server
    are on the same machine -> UI writes the file and DropWatch reloads."""
    path = path or default_watchlist_path()
    name = name.strip()
    is_want = which == "want"

    def _is_header(ln: str, want: bool) -> bool:
        up = ln.strip().upper()
        if want:
            return up.startswith("[WANT")
        return up.startswith("[DON'T WANT") or up.startswith("[NÃO QUERO")

    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError):
        lines = ["[WANT ALERT]", "", "[DON'T WANT]", ""]

    low = name.lower()
    lines = [ln for ln in lines if ln.strip().lower() != low]  # remove duplicate

    out: list[str] = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if not inserted and _is_header(ln, is_want):
            out.append(name)
            inserted = True
    if not inserted:  # section didn't exist in the file
        out += ["", "[WANT ALERT]" if is_want else "[DON'T WANT]", name]

    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8")


# Robust dedup for OCR noise:
SIM_THRESHOLD = 0.85   # similarity (0-1) to treat two names as the SAME item
DEDUP_WINDOW = 45      # seconds without seeing the item before alerting again


def _similar(a: str, b: str) -> float:
    """How similar two names are (0-1). 'Blue Stee! Dagger' ~ 'Blue Steel Dagger'."""
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


class DropWatcher:
    """Detect NEW drops with robust dedup for OCR noise.

    Two mechanisms against the problem of the same drop being alerted multiple times:
      - SIMILARITY: 'Blue Stee! Dagger' ~ 'Blue Steel Dagger' count as the
        same item (OCR swaps 1 letter) -> don't re-alert.
      - STABILITY: only alert a name that appeared in 2 CONSECUTIVE reads
        -> cuts garbage fragments that OCR spits out once ('Red', '3.u...').
    Doesn't re-alert while the item is still visible (resets timer on each
    read); releases again if it disappears for DEDUP_WINDOW seconds (= new drop).
    """

    def __init__(self, watchlist_path):
        self.watchlist_path = watchlist_path
        self.want, self.ignore = load_watchlist(watchlist_path)
        self._prev: set[str] = set()           # nomes da leitura anterior (estabilidade)
        self._alerted: dict[str, float] = {}   # nome alertado -> ultima vez visto (dedup do alerta)
        self._visible_counts: dict[str, int] = {}  # nome -> qtd visivel na ultima leitura (contagem)
        self.box_full: bool = False            # 'Your item box is full.' visivel na ultima leitura

    def reload_watchlist(self):
        self.want, self.ignore = load_watchlist(self.watchlist_path)

    @staticmethod
    def _match(name: str, candidates) -> str | None:
        """Primeiro candidato parecido o bastante com `name` (ou None)."""
        for c in candidates:
            if _similar(name, c) >= SIM_THRESHOLD:
                return c
        return None

    def _dedup_within(self, items: list[str]) -> list[str]:
        """Remove variantes do MESMO item dentro de UMA leitura (mantem o 1o)."""
        unique: list[str] = []
        for name in items:
            if not self._match(name, unique):
                unique.append(name)
        return unique

    def _count_occurrences(self, items: list[str]) -> dict[str, int]:
        """{nome_canonico: quantas vezes aparece agora}, agrupando variantes de OCR (fuzzy)."""
        counts: dict[str, int] = {}
        for name in items:
            key = self._match(name, counts.keys()) or name
            counts[key] = counts.get(key, 0) + 1
        return counts

    def prime(self, client: "AbstractClientWindow") -> None:
        """Mark everything already on screen as 'already seen' -> don't alert NOR count at start."""
        text = read_chat_text(client) or ""
        raw = extract_item_names(text)
        items = self._dedup_within(raw)
        now = time.time()
        self._alerted = {n: now for n in items}
        self._prev = set(items)
        self._visible_counts = self._count_occurrences(raw)
        self.box_full = chat_says_box_full(text)

    def poll(self, client: "AbstractClientWindow") -> tuple[list[tuple[str, str]], dict[str, int]]:
        """Returns (alerts, deltas):
          - alerts: [(name, category)] to alert on Discord -- with DEDUP (don't spam the
            same item in the window).
          - deltas: {name: n} NEW drops to add to the dashboard -- COUNTS repetitions
            (2 identical visible lines = +2; re-reading the same lines doesn't re-count).
        Also updates self.box_full ('Your item box is full.' on the same read)."""
        text = read_chat_text(client)
        if text is None:
            return [], {}
        raw = extract_item_names(text)
        self.box_full = chat_says_box_full(text)
        now = time.time()

        # COUNTING (dashboard): sum the VISIBLE occurrence INCREASES per item.
        cur_counts = self._count_occurrences(raw)
        deltas: dict[str, int] = {}
        for name, cnt in cur_counts.items():
            prev = self._visible_counts.get(self._match(name, self._visible_counts.keys()) or name, 0)
            if cnt > prev:
                deltas[name] = cnt - prev
        self._visible_counts = cur_counts

        # ALERTS (Discord): dedup -- don't re-alert the same item within the window.
        self._alerted = {n: t for n, t in self._alerted.items() if now - t < DEDUP_WINDOW}
        items = self._dedup_within(raw)
        alerts: list[tuple[str, str]] = []
        for name in items:
            if (hit := self._match(name, self._alerted.keys())):
                self._alerted[hit] = now           # continua visivel -> renova timer
                continue
            if not self._match(name, self._prev):  # estabilidade: tem que ter aparecido antes
                continue
            self._alerted[name] = now
            alerts.append((name, classify(name, self.want, self.ignore)))
        self._prev = set(items)
        return alerts, deltas
