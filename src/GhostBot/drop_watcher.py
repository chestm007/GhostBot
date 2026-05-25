"""
Deteccao de drop pelo chat System do TO via OCR (Tesseract).

Fluxo:
  captura a janela -> acha a ANCORA (3 icones do chat) -> recorta a regiao de
  leitura (offsets calibrados) -> trata a imagem (cinza+ampliar+Otsu) -> OCR
  -> extrai nomes de item das linhas "You got the item: [Nome(lvl X)]".

Calibracao inicial (2026-05-25, janela do dono): ancora 64x24; regiao relativa
ao top-left da ancora. Cada jogador pode recalibrar com
`tools/calibrate_chat_region.py` (os offsets viram config por jogador na UI
mais pra frente).
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
import pytesseract

from GhostBot import logger

# pytesseract loga a linha de comando inteira a cada chamada (INFO) -> poluicao.
# Como lemos o chat de poucos em poucos segundos, isso entope o log. Silencia.
logging.getLogger("pytesseract").setLevel(logging.WARNING)

if TYPE_CHECKING:
    from GhostBot.abstract_client_window import AbstractClientWindow

_path_base = os.path.dirname(__file__)


# ----------------------------------------------------------------------------
# Tesseract: nao fica no PATH por padrao. Procura o .exe instalado, e tambem
# uma copia embutida no pacote (pro futuro .exe que distribuimos pros amigos).
# ----------------------------------------------------------------------------
def _find_tesseract() -> str | None:
    candidates = [
        os.path.join(_path_base, "Tesseract-OCR", "tesseract.exe"),  # copia embutida (futuro)
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    return next((c for c in candidates if os.path.exists(c)), None)


_TESS = _find_tesseract()
if _TESS:
    pytesseract.pytesseract.tesseract_cmd = _TESS
else:
    logger.warning("drop_watcher :: Tesseract nao encontrado -- OCR de drop vai falhar")

_TESS_CONFIG = "--psm 6"  # bloco uniforme de texto (varias linhas de chat)

# ----------------------------------------------------------------------------
# Regiao de leitura: offsets relativos ao TOP-LEFT da ancora (calibrado).
# (left, top, right, bottom) -> x in [ax+left, ax+right], y in [ay+top, ay+bottom]
# ----------------------------------------------------------------------------
ANCHOR_BMP = os.path.join(_path_base, "Images", "misc", "chat_anchor.bmp")
ANCHOR_THRESHOLD = 0.80
OCR_REGION_OFFSETS = (0, -158, 378, 0)

# ----------------------------------------------------------------------------
# Extracao de nome de item das linhas do chat
# ----------------------------------------------------------------------------
# Caso ideal: "got the item: [Nome]" / "[Nome(lvl X)]"
_ITEM_RE = re.compile(r"got the item:\s*[\[\(]\s*(.+?)\s*[\]\)]", re.IGNORECASE)
# Fallback: o OCR embola o prefixo "got the item" mas le o "[nome]" certo.
# Tolera [<->( e ]<->), e pula um "(lvl N)" opcional antes do fechamento.
_BRACKET_RE = re.compile(
    r"[\[\(]\s*([A-Za-z][A-Za-z '\-]{1,30}?)\s*(?:\(lvl\s*\d+\))?\s*[\]\)]"
)
_LVL_RE = re.compile(r"\s*\(lvl\s*\d+\)\s*$", re.IGNORECASE)


def _clean(raw: str) -> str:
    return _LVL_RE.sub("", raw).strip()


def extract_item_names(text: str) -> list[str]:
    """Pega os nomes de item das linhas de drop no texto lido pelo OCR.

    Linhas tipo "Congratulations! [Jogador]" tambem tem colchete mas NAO sao
    item -- sao ignoradas.
    """
    names: list[str] = []
    for line in text.splitlines():
        if (m := _ITEM_RE.search(line)):
            names.append(_clean(m.group(1)))
            continue
        if "congrat" in line.lower():
            continue
        for raw in _BRACKET_RE.findall(line):
            if (name := _clean(raw)):
                names.append(name)
    return names


def _preprocess(bgr):
    """Tratamento B (vencedor nos testes): cinza + ampliar 4x + Otsu."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    big = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    _, thr = cv2.threshold(big, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if np.mean(thr) < 127:  # texto claro sobre fundo escuro -> inverte
        thr = cv2.bitwise_not(thr)
    return thr


def find_anchor_top_left(client: "AbstractClientWindow") -> tuple[int, int] | None:
    """Top-left da ancora (3 icones do chat) na janela. None se nao achar
    (chat fechado, aba diferente, janela coberta...)."""
    tmpl = cv2.imread(ANCHOR_BMP, cv2.IMREAD_GRAYSCALE)
    if tmpl is None:
        logger.error("drop_watcher :: ancora bmp nao encontrada: %s", ANCHOR_BMP)
        return None
    win = client.capture_window()  # grayscale, como o resto do bot
    res = cv2.matchTemplate(win, tmpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, (x, y) = cv2.minMaxLoc(res)
    if score < ANCHOR_THRESHOLD:
        logger.debug("drop_watcher :: ancora score baixo %.3f (<%.2f)", score, ANCHOR_THRESHOLD)
        return None
    return x, y


def read_chat_items(client: "AbstractClientWindow") -> list[str] | None:
    """Le a regiao do chat e devolve os nomes de item detectados.
    None = ancora nao achada (nao da pra ler agora)."""
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
        return []
    crop = color[y1:y2, x1:x2]
    text = pytesseract.image_to_string(_preprocess(crop), config=_TESS_CONFIG)
    return extract_item_names(text)


# ----------------------------------------------------------------------------
# Watchlist (alertas_drop.txt)
# ----------------------------------------------------------------------------
def load_watchlist(path) -> tuple[set[str], set[str]]:
    """Le o alertas_drop.txt -> (quero, nao_quero) em minusculo."""
    want: set[str] = set()
    ignore: set[str] = set()
    target: set[str] | None = None
    try:
        for raw in Path(path).read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            up = line.upper()
            if up.startswith("[QUERO"):
                target = want
                continue
            if up.startswith("[NAO QUERO") or up.startswith("[NÃO QUERO"):
                target = ignore
                continue
            if target is not None:
                target.add(line.lower())
    except FileNotFoundError:
        logger.warning("drop_watcher :: watchlist nao encontrada: %s", path)
    return want, ignore


def classify(name: str, want: set[str], ignore: set[str]) -> str:
    """'want' | 'ignore' | 'unknown'."""
    n = name.lower()
    if n in want:
        return "want"
    if n in ignore:
        return "ignore"
    return "unknown"


class DropWatcher:
    """Mantem a watchlist + estado de dedup. `poll(client)` devolve os itens
    NOVOS desde a ultima leitura, ja classificados."""

    def __init__(self, watchlist_path):
        self.watchlist_path = watchlist_path
        self.want, self.ignore = load_watchlist(watchlist_path)
        self._last_seen: set[str] = set()

    def reload_watchlist(self):
        self.want, self.ignore = load_watchlist(self.watchlist_path)

    def poll(self, client: "AbstractClientWindow") -> list[tuple[str, str]]:
        """[(nome, categoria)] dos itens novos. Dedup: compara o conjunto de
        nomes visiveis agora com o da leitura anterior; reporta os que
        apareceram (some quando a linha sai da tela e re-alerta se cair de novo)."""
        items = read_chat_items(client)
        if items is None:
            return []
        current = set(items)
        new = current - self._last_seen
        self._last_seen = current
        out: list[tuple[str, str]] = []
        emitted: set[str] = set()
        for name in items:  # preserva a ordem de cima->baixo
            if name in new and name not in emitted:
                emitted.add(name)
                out.append((name, classify(name, self.want, self.ignore)))
        return out
