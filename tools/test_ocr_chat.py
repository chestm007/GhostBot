"""
Teste/tuning de OCR do chat System do TO.

Objetivo: descobrir qual TRATAMENTO de imagem faz o Tesseract ler melhor as
linhas de drop ("You got the item: [Nome(lvl X)]") e extrair o NOME do item.

Roda em cima de uma IMAGEM JA SALVA (um recorte do chat ou a janela inteira),
NAO precisa do jogo aberto -- e so pra calibrar o pre-processamento.

Uso:
    python tools/test_ocr_chat.py [caminho_da_imagem]

Se nao passar caminho, usa a amostra de teste (tmp_ocr_sample_animalfur.png).
"""
import os
import re
import sys

import cv2
import numpy as np
import pytesseract

# --- Tesseract nao fica no PATH por padrao; aponta pro .exe instalado ---
_TESS_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
]
for _c in _TESS_CANDIDATES:
    if os.path.exists(_c):
        pytesseract.pytesseract.tesseract_cmd = _c
        break

# psm 6 = "assume um bloco uniforme de texto" (bom pra varias linhas de chat)
_TESS_CONFIG = "--psm 6"

# Casa "got the item:" seguido do nome entre [colchetes] OU (parenteses) --
# tolera o erro classico do OCR de trocar '[' por '('. Captura ate o
# fechamento ']' ou ')'.
_ITEM_RE = re.compile(r"got the item:\s*[\[\(]\s*(.+?)\s*[\]\)]", re.IGNORECASE)
# Fallback: QUALQUER coisa entre colchetes/parenteses (o OCR le o '[' e o nome
# de forma confiavel, mas embola o prefixo "got the item"). Tolera [ <-> ( e ] <-> ).
_BRACKET_RE = re.compile(r"[\[\(]\s*([A-Za-z][A-Za-z '\-]{2,30}?)\s*[\]\)]")
# Remove o sufixo "(lvl N)" quando existe (ex.: "Healing Potion(lvl 4)")
_LVL_RE = re.compile(r"\s*\(lvl\s*\d+\)\s*$", re.IGNORECASE)


def _clean(raw: str) -> str:
    return _LVL_RE.sub("", raw).strip()


def extract_item_names(text: str) -> list[str]:
    """Pega os nomes de item das linhas de drop no texto lido pelo OCR.

    Estrategia: primeiro tenta o prefixo exato "got the item: [..]"; se falhar
    (OCR emborou o prefixo), cai pro fallback de colchetes, ignorando linhas que
    parecem "Congratulations [Jogador]" (que tambem tem colchete mas nao e item).
    """
    names = []
    for line in text.splitlines():
        if (m := _ITEM_RE.search(line)):
            names.append(_clean(m.group(1)))
            continue
        if "congrat" in line.lower():  # "Congratulations! [Jogador]..." -> nao e item
            continue
        for raw in _BRACKET_RE.findall(line):
            if (name := _clean(raw)):
                names.append(name)
    return names


def upscale(img, factor=4):
    return cv2.resize(img, None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC)


def prep_gray_otsu(bgr):
    """Tratamento B: cinza + ampliar + binarizacao Otsu (texto preto, fundo branco)."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    big = upscale(gray)
    _, thr = cv2.threshold(big, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # texto do TO e claro sobre fundo escuro -> inverte pra ficar texto preto
    if np.mean(thr) < 127:
        thr = cv2.bitwise_not(thr)
    return thr


def prep_bright_mask(bgr):
    """Tratamento C: isola SO o texto claro (alto brilho) e descarta o cenario.

    O texto do chat e claro/saturado; o mato de fundo e mais escuro.
    Pegamos pixels com brilho alto -> mascara limpa, independente da cor exata
    (serve pra qualquer raridade)."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    v = hsv[..., 2]
    # brilho acima de ~150 = provavelmente texto
    mask = cv2.inRange(v, 150, 255)
    big = upscale(mask)
    # texto branco sobre preto -> inverte pra texto preto sobre branco (Tesseract gosta)
    return cv2.bitwise_not(big)


def run(label, image, save_name=None):
    text = pytesseract.image_to_string(image, config=_TESS_CONFIG)
    items = extract_item_names(text)
    print(f"\n{'='*60}\n[{label}]\n{'='*60}")
    print(text.strip())
    print(f"  -> ITENS DETECTADOS: {items if items else '(nenhum)'}")
    if save_name:
        out = os.path.join(os.path.dirname(__file__), "..", save_name)
        cv2.imwrite(out, image)
        print(f"  (imagem tratada salva em {os.path.normpath(out)})")
    return items


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Bot\BotTO\tmp_ocr_sample_animalfur.png"
    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise SystemExit(f"Nao consegui abrir a imagem: {path}")
    print(f"Imagem: {path}  shape={bgr.shape}")

    run("A - CRUA (sem tratamento)", bgr)
    run("B - CINZA + AMPLIAR + OTSU", prep_gray_otsu(bgr), "tmp_ocr_B.png")
    run("C - ISOLAR TEXTO CLARO (bright mask)", prep_bright_mask(bgr), "tmp_ocr_C.png")


if __name__ == "__main__":
    main()
