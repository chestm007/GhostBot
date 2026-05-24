"""
Teste ROBUSTO do surroundings via ancora (template) + offsets.

Mesmo esquema do dialog de venda do NPC:
  1. Acha o titulo "Surroundings" na tela via template matching
     (Images/misc/surroundings_title.bmp) -- funciona em QUALQUER posicao.
  2. A partir do centro do titulo, calcula:
       - campo de busca dourado  = titulo + TITLE_TO_SEARCH
       - 1o resultado da lista    = titulo + TITLE_TO_FIRST_RESULT
  3. Clica no campo, digita SEARCH_TERM.
  4. (se STOP_AFTER_TYPE=False) clica no 1o resultado e faz polling
     de posicao ate chegar perto do alvo -- prova que navegou.

NAO mexe no codigo de producao. NAO vende nada.
"""
import os
import time
import cv2
import numpy as np
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.lib.math import linear_distance

# ---- Config ----
TITLE_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\surroundings_title.bmp"
TITLE_MATCH_THRESHOLD = 0.70
TITLE_TO_SEARCH = (140, 347)        # titulo -> campo de busca dourado (calibrado via cursor)
TITLE_TO_FIRST_RESULT = (-106, 70)  # titulo -> 1a linha da lista (calibrado via cursor)
SEARCH_TERM = "Blacksmith"
TARGET_LOCATION = (365, 1093)       # onde o Blacksmith fica (pra confirmar navegacao)
ARRIVAL_THRESHOLD = 2
MAX_WAIT_SECONDS = 60
STATIONARY_TIMEOUT_S = 6

STOP_AFTER_TYPE = False  # True = so busca+digita+captura (calibracao). False = clica resultado e navega.


def find_title_center(client):
    """Acha o titulo Surroundings na tela. Retorna ((cx,cy), score) ou (None, score)."""
    bmp = cv2.imread(TITLE_BMP, cv2.IMREAD_GRAYSCALE)
    if bmp is None:
        raise SystemExit(f"BMP do titulo nao encontrado: {TITLE_BMP}")
    win = client.capture_window()  # grayscale 2D
    res = cv2.matchTemplate(win, bmp, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(res)
    h, w = bmp.shape[:2]
    if mv < TITLE_MATCH_THRESHOLD:
        return None, mv
    return (ml[0] + w // 2, ml[1] + h // 2), mv


def main():
    proc = next(iter(PymemProcess.list_clients()), None)
    if proc is None:
        raise SystemExit("client.exe nao encontrado")
    client = Win32ClientWindow(proc)
    ww, wh = client.get_window_size()
    print(f"Janela: {ww} x {wh}")

    # 1) tenta achar o titulo (painel ja aberto?). Se nao, abre e tenta de novo.
    center, score = find_title_center(client)
    if center is None:
        print(f"Titulo nao achado (score {score:.3f}) -- abrindo painel surroundings...")
        client.open_surroundings_ui()
        time.sleep(1.5)
        center, score = find_title_center(client)
    if center is None:
        raise SystemExit(f">>> FALHOU: titulo nao achado mesmo apos abrir (score {score:.3f})")
    print(f"Titulo 'Surroundings' achado em {center}  (score {score:.3f})")

    search_pos = (center[0] + TITLE_TO_SEARCH[0], center[1] + TITLE_TO_SEARCH[1])
    result_pos = (center[0] + TITLE_TO_FIRST_RESULT[0], center[1] + TITLE_TO_FIRST_RESULT[1])
    print(f"Campo de busca calculado: {search_pos}")
    print(f"1o resultado calculado:   {result_pos}")

    # 2) clica no campo e digita
    print(f"Clicando no campo de busca e digitando '{SEARCH_TERM}'...")
    client.left_click(search_pos)
    time.sleep(0.5)
    for _ in range(15):                 # limpa qualquer texto anterior no campo
        client.press_key('backspace')
    time.sleep(0.3)
    client.type_keys(SEARCH_TERM)
    time.sleep(1.0)

    # 3) captura pra conferencia
    out = r"C:\Bot\BotTO\tmp_after_search.png"
    cv2.imwrite(out, client.capture_window(color=True))
    print(f"Screenshot pos-busca salvo em {out}")

    if STOP_AFTER_TYPE:
        print(">>> STOP_AFTER_TYPE=True: parando aqui pra conferir o screenshot.")
        return

    # 4) clica no resultado e confirma navegacao
    print(f"Clicando no 1o resultado em {result_pos}...")
    client.left_click(result_pos)

    t0 = time.time()
    last_loc = None
    stationary_t = None
    arrived = False
    while time.time() - t0 < MAX_WAIT_SECONDS:
        cur = client.location
        dist = linear_distance(cur, TARGET_LOCATION)
        print(f"  loc={cur}  dist={dist:.1f}")
        if dist < ARRIVAL_THRESHOLD:
            print(f"  >>> CHEGOU! dist={dist:.1f}")
            arrived = True
            break
        if last_loc is not None and linear_distance(cur, last_loc) < 1:
            if stationary_t is None:
                stationary_t = time.time()
            elif time.time() - stationary_t > STATIONARY_TIMEOUT_S:
                print(f"  >>> PAROU sem chegar (dist={dist:.1f}). Abortando.")
                break
        else:
            stationary_t = None
        last_loc = cur
        time.sleep(1)
    else:
        print(f"  >>> TIMEOUT {MAX_WAIT_SECONDS}s")

    print("CHEGOU" if arrived else "NAO CHEGOU")

    # 5) fecha o painel surroundings (segundo clique no olho do minimapa)
    if arrived:
        print("Fechando painel surroundings (2o clique no olho do minimapa)...")
        client.open_surroundings_ui()   # open_surroundings_ui = toggle do olho


if __name__ == "__main__":
    main()
