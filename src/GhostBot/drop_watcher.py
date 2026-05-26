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

import difflib
import logging
import os
import re
import time
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


def tesseract_available() -> bool:
    return _TESS is not None

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
    r"[\[\(]\s*([A-Za-z][A-Za-z '\-]{3,40}?)\s*(?:\(lvl\s*\d+\))?\s*[\]\)]"
)
_LVL_RE = re.compile(r"\s*\(lvl\s*\d+\)\s*$", re.IGNORECASE)

MIN_NAME_LEN = 4  # item de verdade tem nome >= 4 letras; corta fragmentos ('XY', 'Red')


def _clean(raw: str) -> str:
    return _LVL_RE.sub("", raw).strip()


def _looks_like_item(name: str) -> bool:
    return len(name) >= MIN_NAME_LEN


def extract_item_names(text: str) -> list[str]:
    """Pega os nomes de item das linhas de drop no texto lido pelo OCR.

    Linhas tipo "Congratulations! [Jogador]" tambem tem colchete mas NAO sao
    item -- sao ignoradas. Fragmentos curtos de ruido de OCR sao descartados.
    """
    names: list[str] = []
    for line in text.splitlines():
        if (m := _ITEM_RE.search(line)):
            if _looks_like_item(name := _clean(m.group(1))):
                names.append(name)
            continue
        if "congrat" in line.lower():
            continue
        for raw in _BRACKET_RE.findall(line):
            if _looks_like_item(name := _clean(raw)):
                names.append(name)
    return names


# ----------------------------------------------------------------------------
# Deteccao de "mochila cheia" -- MESMA regiao do chat (mesma leitura OCR).
# Frase do jogo: "Your item box is full." O OCR embola letras, entao normaliza
# a linha pra so-letras e casa o nucleo distintivo ('item box is full').
# ----------------------------------------------------------------------------
_BOX_FULL_CORE = "itemboxisfull"
# O OCR troca letra<->digito (o->0, l->1, e->3...). Desfaz as trocas comuns
# ANTES de comparar, senao 'Y0ur 1tem b0x is fu11' nao casa com 'item box is full'.
_OCR_DIGIT_FIX = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s", "8": "b", "!": "l", "|": "l"})
_BOX_FULL_SIM = 0.72  # limiar de semelhanca (nucleo distintivo -> seguro contra falso positivo)


def chat_says_box_full(text: str) -> bool:
    """True se alguma linha do chat parece 'Your item box is full.'
    (nucleo 'itemboxisfull' como substring OU semelhanca >= limiar; tolera ruido de OCR)."""
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


def read_chat_text(client: "AbstractClientWindow") -> str | None:
    """Le a regiao do chat e devolve o TEXTO BRUTO do OCR.
    None = ancora nao achada (nao da pra ler agora); "" = regiao vazia.
    Base comum: 1 leitura serve pra drops E pra 'mochila cheia'."""
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
    """Nomes de item detectados no chat. None = ancora nao achada."""
    text = read_chat_text(client)
    if text is None:
        return None
    return extract_item_names(text)


# ----------------------------------------------------------------------------
# Watchlist (alertas_drop.txt)
# ----------------------------------------------------------------------------
_WATCHLIST_CANDIDATES = [
    os.path.join(os.path.expanduser("~"), "GhostBot", "alertas_drop.txt"),
    os.path.normpath(os.path.join(_path_base, "..", "..", "alertas_drop.txt")),
    os.path.join(_path_base, "alertas_drop.txt"),
]


def default_watchlist_path() -> str:
    """Acha o alertas_drop.txt (HOME/GhostBot, depois raiz do repo/.exe)."""
    for p in _WATCHLIST_CANDIDATES:
        if os.path.exists(p):
            return p
    return _WATCHLIST_CANDIDATES[0]  # default: HOME/GhostBot (criado por quem usar)


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


def add_to_watchlist(name: str, which: str, path=None) -> None:
    """Adiciona `name` na secao 'want' (QUERO) ou 'ignore' (NAO QUERO) do
    alertas_drop.txt, tirando de onde estava antes (sem duplicar). UI e server
    ficam na mesma maquina -> a UI escreve o arquivo e o DropWatch recarrega."""
    path = path or default_watchlist_path()
    name = name.strip()
    is_want = which == "want"

    def _is_header(ln: str, want: bool) -> bool:
        up = ln.strip().upper()
        if want:
            return up.startswith("[QUERO")
        return up.startswith("[NAO QUERO") or up.startswith("[NÃO QUERO")

    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError):
        lines = ["[QUERO ALERTA]", "", "[NAO QUERO]", ""]

    low = name.lower()
    lines = [ln for ln in lines if ln.strip().lower() != low]  # tira duplicata

    out: list[str] = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if not inserted and _is_header(ln, is_want):
            out.append(name)
            inserted = True
    if not inserted:  # secao nao existia no arquivo
        out += ["", "[QUERO ALERTA]" if is_want else "[NAO QUERO]", name]

    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8")


# Dedup robusto a ruido de OCR:
SIM_THRESHOLD = 0.85   # similaridade (0-1) p/ tratar dois nomes como o MESMO item
DEDUP_WINDOW = 45      # segundos sem ver o item antes de poder alertar de novo


def _similar(a: str, b: str) -> float:
    """Quao parecidos dois nomes sao (0-1). 'Blue Stee! Dagger' ~ 'Blue Steel Dagger'."""
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


class DropWatcher:
    """Detecta drops NOVOS com dedup robusto a ruido de OCR.

    Dois mecanismos contra o problema de o mesmo drop ser avisado varias vezes:
      - SEMELHANCA: 'Blue Stee! Dagger' ~ 'Blue Steel Dagger' contam como o
        mesmo item (OCR troca 1 letra) -> nao re-alerta.
      - ESTABILIDADE: so alerta um nome que apareceu em 2 leituras SEGUIDAS
        -> corta fragmentos de lixo que o OCR cospe 1 vez so ('Red', '3.u...').
    Nao re-alerta enquanto o item continua visivel (renova o timer a cada
    leitura); libera de novo se ele sumir por DEDUP_WINDOW segundos (= novo drop).
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
        """Marca tudo que ja esta na tela como 'ja visto' -> nao alerta NEM conta no inicio."""
        text = read_chat_text(client) or ""
        raw = extract_item_names(text)
        items = self._dedup_within(raw)
        now = time.time()
        self._alerted = {n: now for n in items}
        self._prev = set(items)
        self._visible_counts = self._count_occurrences(raw)
        self.box_full = chat_says_box_full(text)

    def poll(self, client: "AbstractClientWindow") -> tuple[list[tuple[str, str]], dict[str, int]]:
        """Retorna (alerts, deltas):
          - alerts: [(nome, categoria)] pra avisar no Discord -- com DEDUP (nao spamma o
            mesmo item na janela).
          - deltas: {nome: n} drops NOVOS pra somar no dashboard -- CONTA repeticoes
            (2 linhas iguais visiveis = +2; reler as mesmas linhas nao re-conta).
        Tambem atualiza self.box_full ('Your item box is full.' na mesma leitura)."""
        text = read_chat_text(client)
        if text is None:
            return [], {}
        raw = extract_item_names(text)
        self.box_full = chat_says_box_full(text)
        now = time.time()

        # CONTAGEM (dashboard): soma os AUMENTOS de ocorrencia visivel por item.
        cur_counts = self._count_occurrences(raw)
        deltas: dict[str, int] = {}
        for name, cnt in cur_counts.items():
            prev = self._visible_counts.get(self._match(name, self._visible_counts.keys()) or name, 0)
            if cnt > prev:
                deltas[name] = cnt - prev
        self._visible_counts = cur_counts

        # ALERTAS (Discord): dedup -- nao re-alerta o mesmo item dentro da janela.
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
