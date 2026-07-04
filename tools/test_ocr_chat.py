"""
OCR test/tuning for the TO System chat.

Goal: discover which IMAGE TREATMENT makes Tesseract read drop lines best
("You got the item: [Name(lvl X)]") and extract the ITEM NAME.

Runs on a SAVED IMAGE (a crop of the chat or the full window),
does NOT need the game open -- just for calibrating preprocessing.

Usage:
    python tools/test_ocr_chat.py [image_path]

If no path is given, uses the test sample (tmp_ocr_sample_animalfur.png).
"""
import os
import re
import sys

import cv2
import numpy as np
import pytesseract

from GhostBot.lib.text_utils import clean_item_name

_TESS_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
]
for _c in _TESS_CANDIDATES:
    if os.path.exists(_c):
        pytesseract.pytesseract.tesseract_cmd = _c
        break

# psm 6 = "assume a uniform text block" (good for multiple chat lines)
_TESS_CONFIG = "--psm 6"

# Match "got the item:" followed by name in [brackets] OR (parens) --
# tolerates the classic OCR error of swapping '[' for '('. Captures up to
# the closing ']' or ')'.
_ITEM_RE = re.compile(r"got the item:\s*[\[\(]\s*(.+?)\s*[\]\)]", re.IGNORECASE)
# Fallback: ANYTHING in brackets/parens (OCR reads the '[' and name
# reliably, but messes up the "got the item:" prefix). Tolerates [ <-> ( and ] <-> ).
_BRACKET_RE = re.compile(r"[\[\(]\s*([A-Za-z][A-Za-z '\-]{2,30}?)\s*[\]\)]")

def extract_item_names(text: str) -> list[str]:
    """Extract item names from drop lines in the text read by OCR.

    Strategy: first try the exact prefix "got the item: [..]"; if that fails
    (OCR messed up the prefix), fall back to bracket matching, ignoring lines
    that look like "Congratulations [Player]" (which also has brackets but isn't an item).
    """
    names = []
    for line in text.splitlines():
        if (m := _ITEM_RE.search(line)):
            names.append(clean_item_name(m.group(1)))
            continue
        if "congrat" in line.lower():  # "Congratulations! [Player]..." -> not an item
            continue
        for raw in _BRACKET_RE.findall(line):
            if (name := clean_item_name(raw)):
                names.append(name)
    return names


def upscale(img, factor=4):
    return cv2.resize(img, None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC)


def prep_gray_otsu(bgr):
    """Treatment B: gray + upscale + Otsu binarization (black text, white background)."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    big = upscale(gray)
    _, thr = cv2.threshold(big, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # TO text is light on dark background -> invert to get black text
    if np.mean(thr) < 127:
        thr = cv2.bitwise_not(thr)
    return thr


def prep_bright_mask(bgr):
    """Treatment C: isolate ONLY light text (high brightness) and discard the background.

    Chat text is bright/saturated; the grass background is darker.
    We take high-brightness pixels -> clean mask, independent of exact color
    (works for any rarity)."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    v = hsv[..., 2]
    # brightness above ~150 = likely text
    mask = cv2.inRange(v, 150, 255)
    big = upscale(mask)
    # white text on black -> invert to black text on white (Tesseract likes it)
    return cv2.bitwise_not(big)


def run(label, image, save_name=None):
    text = pytesseract.image_to_string(image, config=_TESS_CONFIG)
    items = extract_item_names(text)
    print(f"\n{'='*60}\n[{label}]\n{'='*60}")
    print(text.strip())
    print(f"  -> ITEMS DETECTED: {items if items else '(none)'}")
    if save_name:
        out = os.path.join(os.path.dirname(__file__), "..", save_name)
        cv2.imwrite(out, image)
        print(f"  (processed image saved to {os.path.normpath(out)})")
    return items


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Bot\BotTO\tmp_ocr_sample_animalfur.png"
    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise SystemExit(f"Could not open the image: {path}")
    print(f"Image: {path}  shape={bgr.shape}")

    run("A - RAW (no treatment)", bgr)
    run("B - GRAY + UPSCALE + OTSU", prep_gray_otsu(bgr), "tmp_ocr_B.png")
    run("C - ISOLATE BRIGHT TEXT (bright mask)", prep_bright_mask(bgr), "tmp_ocr_C.png")


if __name__ == "__main__":
    main()
