"""
CICLO COMPLETO (DRY) — encadeia tudo que validamos, sem vender de verdade:

  1. NAVEGAR ate o NPC (surroundings: abre painel -> busca -> 1o resultado -> chega)
  2. ABRIR VENDA (reset camera -> right-click NPC -> "Dialogue" -> "Sell Item")
  3. VENDER (acha "Sell" -> 30 cliques no slot 1)  [DRY: NAO confirma]
  4. FECHAR dialog (Esc)
  5. VOLTAR ao spot (abre mapa -> isca + spot -> fecha mapa -> espera chegar)

Tudo via template+offset, sem coord fixa. Ajuste DRY_CONFIRM=False so quando
quiser vender de verdade.
"""
import time
import cv2
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.lib.math import linear_distance

MISC = r"C:\Bot\BotTO\src\GhostBot\Images\misc"

# --- Surroundings (navegacao) ---
SURR_TITLE_BMP = MISC + r"\surroundings_title.bmp"
TITLE_TO_SEARCH = (140, 347)
TITLE_TO_FIRST_RESULT = (-106, 70)
SEARCH_TERM = "Blacksmith"
NPC_LOCATION = (365, 1093)

# --- Janela Dialogue do NPC ---
DIALOGUE_BMP = MISC + r"\npc_dialogue_title.bmp"
DIALOGUE_TO_SELL_ITEM = (-114, 181)

# --- Dialog de venda ---
SELL_HEADER_BMP = MISC + r"\npc_sell_dialog_header.bmp"
HEADER_TO_SLOT1 = (-97, 43)
HEADER_TO_SELL_CONFIRM = (-76, 461)
SELL_COL_SPACING = 34.4      # grid 6 col x 4 linhas = 24 slots
SELL_ROW_SPACING = 35.333
SELL_START_SLOT = 1          # usuario escolhe (1-24): vende deste em diante, mantem 1..N-1
SLOT_CLICKS = 30


def slot_pos(hdr, n):
    """Posicao do slot n (1-24) do grid de venda, ancorada no header."""
    idx = n - 1
    row, col = idx // 6, idx % 6
    return (int(hdr[0] + HEADER_TO_SLOT1[0] + col * SELL_COL_SPACING),
            int(hdr[1] + HEADER_TO_SLOT1[1] + row * SELL_ROW_SPACING))

# --- Mapa (volta ao spot) ---
MAP_TITLE_BMP = MISC + r"\map_title.bmp"
MAP_TO_SPOT = (-125, 297)
MAP_DUMMY_OFFSET = (60, 0)
SPOT_WORLD = (321, 1147)

ARRIVAL = 3
THRESHOLD = 0.70
STEP_DELAY = 2.0     # delay entre atividades (dar tempo do jogo terminar cada acao)
DRY_CONFIRM = True   # True = NAO clica o Sell de confirmar


def find_center(client, bmp_path, thr=THRESHOLD):
    win = client.capture_window()
    bmp = cv2.imread(bmp_path, cv2.IMREAD_GRAYSCALE)
    res = cv2.matchTemplate(win, bmp, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(res)
    h, w = bmp.shape[:2]
    if mv < thr:
        return None, mv
    return (ml[0] + w // 2, ml[1] + h // 2), mv


def wait_arrival(client, target, timeout=60):
    t0 = time.time()
    last = None
    stat = None
    while time.time() - t0 < timeout:
        cur = client.location
        d = linear_distance(cur, target)
        print(f"    loc={cur} dist={d:.1f}")
        if d < ARRIVAL:
            print(f"    >>> CHEGOU (dist={d:.1f})")
            return True
        if last is not None and linear_distance(cur, last) < 1:
            if stat is None:
                stat = time.time()
            elif time.time() - stat > 5:
                print(f"    >>> parou sem chegar (dist={d:.1f})")
                return False
        else:
            stat = None
        last = cur
        time.sleep(1)
    print("    >>> TIMEOUT")
    return False


def navigate_to_npc(client):
    print("[1] NAVEGAR ate o NPC")
    title, score = find_center(client, SURR_TITLE_BMP)
    if title is None:
        print(f"    painel fechado (score {score:.3f}) -> abrindo")
        client.open_surroundings_ui()
        time.sleep(1.5)
        title, score = find_center(client, SURR_TITLE_BMP)
    if title is None:
        raise SystemExit(f"    FALHOU: 'Surroundings' nao achado (score {score:.3f})")
    print(f"    'Surroundings' em {title} (score {score:.3f})")
    search = (title[0] + TITLE_TO_SEARCH[0], title[1] + TITLE_TO_SEARCH[1])
    result = (title[0] + TITLE_TO_FIRST_RESULT[0], title[1] + TITLE_TO_FIRST_RESULT[1])
    client.left_click(search)
    time.sleep(0.4)
    for _ in range(15):
        client.press_key('backspace')
    time.sleep(0.3)
    client.type_keys(SEARCH_TERM)
    time.sleep(1.0)
    client.left_click(result)
    if not wait_arrival(client, NPC_LOCATION):
        raise SystemExit("    FALHOU: nao chegou no NPC")
    print(f"    esperando o char parar de vez ({STEP_DELAY}s)...")
    time.sleep(STEP_DELAY)
    client.open_surroundings_ui()  # fecha painel
    time.sleep(STEP_DELAY)


def open_sell_dialog(client):
    print("[2] ABRIR VENDA")
    time.sleep(STEP_DELAY)            # deixa o char assentar antes
    client.reset_camera()
    time.sleep(STEP_DELAY)
    client.click_npc()
    time.sleep(STEP_DELAY)
    dlg, score = find_center(client, DIALOGUE_BMP)
    if dlg is None:
        raise SystemExit(f"    FALHOU: 'Dialogue' nao achado (score {score:.3f})")
    sell_item = (dlg[0] + DIALOGUE_TO_SELL_ITEM[0], dlg[1] + DIALOGUE_TO_SELL_ITEM[1])
    print(f"    'Dialogue' em {dlg} (score {score:.3f}) -> Sell Item {sell_item}")
    client.left_click(sell_item)
    time.sleep(STEP_DELAY)
    hdr, hscore = find_center(client, SELL_HEADER_BMP)
    if hdr is None:
        raise SystemExit(f"    FALHOU: dialog de venda nao abriu (header score {hscore:.3f})")
    print(f"    dialog de venda aberto (header {hdr} score {hscore:.3f})")
    return hdr


def sell_page(client, hdr):
    print("[3] VENDER (DRY)" if DRY_CONFIRM else "[3] VENDER")
    start = slot_pos(hdr, SELL_START_SLOT)
    confirm = (hdr[0] + HEADER_TO_SELL_CONFIRM[0], hdr[1] + HEADER_TO_SELL_CONFIRM[1])
    print(f"    slot inicial {SELL_START_SLOT} em {start} | confirm {confirm} -> {SLOT_CLICKS} cliques")
    for _ in range(SLOT_CLICKS):
        client.left_click(start)
        time.sleep(0.2)
    if DRY_CONFIRM:
        print("    [DRY] nao confirma a venda")
    else:
        client.left_click(confirm)
        time.sleep(1.0)
        print("    venda confirmada")
    print("[4] FECHAR dialog (Esc)")
    client.press_key('esc')
    time.sleep(STEP_DELAY)


def return_to_spot(client):
    print("[5] VOLTAR ao spot")
    client.press_key('m')   # abre mapa
    time.sleep(STEP_DELAY)
    title, score = find_center(client, MAP_TITLE_BMP)
    if title is None:
        client.press_key('m')
        time.sleep(STEP_DELAY)
        title, score = find_center(client, MAP_TITLE_BMP)
    if title is None:
        raise SystemExit(f"    FALHOU: mapa/'Map' nao achado (score {score:.3f})")
    spot = (title[0] + MAP_TO_SPOT[0], title[1] + MAP_TO_SPOT[1])
    dummy = (spot[0] + MAP_DUMMY_OFFSET[0], spot[1] + MAP_DUMMY_OFFSET[1])
    print(f"    'Map' em {title} (score {score:.3f}) -> spot {spot} | isca {dummy}")
    client.right_click(dummy)
    time.sleep(0.5)
    client.right_click(spot)
    time.sleep(0.5)
    client.press_key('m')   # fecha mapa
    if not wait_arrival(client, SPOT_WORLD):
        print("    AVISO: nao confirmou chegada no spot")


def main():
    proc = next(iter(PymemProcess.list_clients()), None)
    if proc is None:
        raise SystemExit("client.exe nao encontrado")
    client = Win32ClientWindow(proc)
    print(f"Janela: {client.get_window_size()} | DRY_CONFIRM={DRY_CONFIRM}")
    print(f"Char em {client.location}")
    print()

    navigate_to_npc(client)
    hdr = open_sell_dialog(client)
    sell_page(client, hdr)
    return_to_spot(client)
    print("\n===== CICLO COMPLETO =====")


if __name__ == "__main__":
    main()
