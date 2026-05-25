"""
Calibra a regiao do chat System pro OCR de drop.

A ANCORA (3 icones do chat: balao + cruz + bau) define o canto
INFERIOR-ESQUERDO da area de leitura. Voce so precisa marcar o canto
SUPERIOR-DIREITO com o mouse.

COMO USAR:
  Rode o script. Vai aparecer uma contagem regressiva. Antes de zerar,
  deixe o MOUSE PARADO no canto SUPERIOR-DIREITO da area do chat que voce
  quer ler (ex.: logo depois do fim da linha mais longa, em cima).

O script entao:
  - acha a ancora (3 icones) na janela do jogo,
  - le a posicao do mouse,
  - calcula o retangulo de leitura,
  - mostra o que o OCR le nesse retangulo (pra voce confirmar na hora),
  - imprime os OFFSETS pra eu fixar no codigo.
"""
import os
import sys
import time

# bootstrap: acha o pacote GhostBot sem precisar setar PYTHONPATH na mao
sys.path.insert(0, r"C:\Bot\BotTO\src")
sys.path.insert(0, os.path.dirname(__file__))

import cv2
import numpy as np
import pytesseract
import win32api
import win32gui

from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess
from test_ocr_chat import prep_gray_otsu, extract_item_names  # reusa tratamento B

for _c in (r"C:\Program Files\Tesseract-OCR\tesseract.exe",
           r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
    if os.path.exists(_c):
        pytesseract.pytesseract.tesseract_cmd = _c
        break

ANCHOR_PATH = r"C:\Bot\BotTO\tmp_anchor_template.png"
COUNTDOWN = 7

proc = next(iter(PymemProcess.list_clients()), None)
if proc is None:
    raise SystemExit("client.exe nao encontrado -- o jogo esta aberto?")
client = Win32ClientWindow(proc)
hwnd = client.window_handle

print("=" * 60)
print("  Deixe o MOUSE no canto SUPERIOR-DIREITO da area do chat")
print("  (onde voce quer que a leitura TERMINE), e espere zerar.")
print("=" * 60)
for i in range(COUNTDOWN, 0, -1):
    print(f"  lendo em {i}... ", end="\r", flush=True)
    time.sleep(1)
print("  >>> LENDO AGORA <<<        ")

# cursor em coord de TELA -> coord do CLIENTE (mesmo espaco do capture_window,
# que pega a area do cliente). ScreenToClient ja desconta borda/barra de titulo.
sx, sy = win32api.GetCursorPos()
mx, my = win32gui.ScreenToClient(hwnd, (sx, sy))

win_gray = client.capture_window()           # grayscale, como o bot usa
win_color = client.capture_window(color=True)
cap_h, cap_w = win_gray.shape[:2]

tmpl = cv2.imread(ANCHOR_PATH, cv2.IMREAD_GRAYSCALE)
if tmpl is None:
    raise SystemExit(f"template da ancora nao encontrado: {ANCHOR_PATH}")
res = cv2.matchTemplate(win_gray, tmpl, cv2.TM_CCOEFF_NORMED)
_, score, _, (ax, ay) = cv2.minMaxLoc(res)

print(f"\ncaptura(cliente)={cap_w}x{cap_h}")
print(f"ancora: score={score:.3f}  top-left=({ax},{ay})")
print(f"mouse (coord janela): ({mx},{my})")

# retangulo: esquerda+baixo vem da ancora; direita+cima vem do mouse
x1, y1, x2, y2 = ax, my, mx, ay
if not (x2 > x1 and y2 > y1):
    print("\n(!) Retangulo invalido. O mouse precisa ficar ACIMA e a DIREITA")
    print("    dos icones do chat. Tenta de novo posicionando mais pra cima/direita.")
    raise SystemExit(1)

print(f"\nRETANGULO OCR: x1={x1} y1={y1} x2={x2} y2={y2}  (w={x2-x1} h={y2-y1})")
print(f">>> OFFSETS canto sup-dir relativo a ancora top-left: ({mx-ax}, {my-ay})")

# valida ao vivo: recorta, trata, OCR
crop = win_color[y1:y2, x1:x2]
cv2.imwrite(r"C:\Bot\BotTO\tmp_chat_calib.png", crop)
text = pytesseract.image_to_string(prep_gray_otsu(crop), config="--psm 6")
print("\n=== OCR da regiao calibrada (tratamento B) ===")
print(text.strip())
print(f"\n-> ITENS DETECTADOS: {extract_item_names(text) or '(nenhum)'}")
print("\n(recorte salvo em tmp_chat_calib.png -- manda pra mim conferir)")
