"""
Teste do retorno ao spot via mapa:
  1. Acha o titulo "Map" do mapa aberto via template (ancora)
  2. right-click no spot = titulo + offset
  3. fecha o mapa (tecla M)
  4. poll de location pra confirmar que o char andou

Mapa precisa estar ABERTO antes de rodar. NAO mexe no codigo de producao.
O offset aqui eh um ponto de TESTE -- o real sera escolhido pelo usuario na UI.
"""
import time
import cv2
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.lib.math import linear_distance

MAP_TITLE_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\map_title.bmp"
MAP_TO_SPOT = (-125, 297)   # titulo "Map" -> spot de farm (TESTE; real vem da UI)
MAP_DUMMY_OFFSET = (60, 0)  # clique-isca: spot + isto -> regiao diferente (quebra o bug
                            # do jogo que ignora 2 cliques seguidos no MESMO destino)
SPOT_WORLD = (321, 1147)    # coords do mundo do spot exemplo (lido apos round 1).
                            # NA PRODUCAO: ler client.location no momento que o usuario
                            # define o spot (ele esta farmando ali) e salvar junto com o offset.
ARRIVAL = 3                 # distancia pra considerar "chegou no spot"
THRESHOLD = 0.70


def find_title(client):
    win = client.capture_window()
    bmp = cv2.imread(MAP_TITLE_BMP, cv2.IMREAD_GRAYSCALE)
    res = cv2.matchTemplate(win, bmp, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(res)
    h, w = bmp.shape[:2]
    if mv < THRESHOLD:
        return None, mv
    return (ml[0] + w // 2, ml[1] + h // 2), mv


def main():
    proc = next(iter(PymemProcess.list_clients()), None)
    if proc is None:
        raise SystemExit("client.exe nao encontrado")
    client = Win32ClientWindow(proc)
    print(f"Janela: {client.get_window_size()}")

    title, score = find_title(client)
    if title is None:
        raise SystemExit(f">>> titulo 'Map' nao achado (score {score:.3f}). O mapa esta ABERTO?")
    spot = (title[0] + MAP_TO_SPOT[0], title[1] + MAP_TO_SPOT[1])
    dummy = (spot[0] + MAP_DUMMY_OFFSET[0], spot[1] + MAP_DUMMY_OFFSET[1])
    print(f"Titulo 'Map' em {title} (score {score:.3f}) -> spot em {spot} | isca em {dummy}")

    start = client.location
    d0 = linear_distance(start, SPOT_WORLD)
    print(f"Char comeca em {start} (dist ao spot {d0:.1f})")
    if d0 < ARRIVAL:
        print(">>> AVISO: char ja esta no spot -- anda pra longe antes pra ver o retorno.")
    # clique-isca numa regiao diferente, depois o spot real -> evita o bug do jogo
    print("Right-click ISCA, depois SPOT, e fecha mapa (M)...")
    client.right_click(dummy)
    time.sleep(0.5)
    client.right_click(spot)
    time.sleep(0.5)
    client.press_key('m')   # fecha o mapa pra liberar o movimento

    # timer de chegada: espera o char chegar perto do spot (igual no Blacksmith)
    t0 = time.time()
    last = None
    stationary_t = None
    arrived = False
    while time.time() - t0 < 45:
        cur = client.location
        d = linear_distance(cur, SPOT_WORLD)
        print(f"  loc={cur}  dist_ao_spot={d:.1f}")
        if d < ARRIVAL:
            arrived = True
            print(f"  >>> CHEGOU NO SPOT! dist={d:.1f}")
            break
        if last is not None and linear_distance(cur, last) < 1:
            if stationary_t is None:
                stationary_t = time.time()
            elif time.time() - stationary_t > 4:
                print(f"  >>> parou sem chegar (dist={d:.1f})")
                break
        else:
            stationary_t = None
        last = cur
        time.sleep(1)
    else:
        print("  >>> TIMEOUT")

    print("CHEGOU NO SPOT" if arrived else "NAO CHEGOU")


if __name__ == "__main__":
    main()
