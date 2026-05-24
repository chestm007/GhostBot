"""
Teste do fluxo completo + chegada confirmada no Blacksmith:

1. Abre Surroundings
2. Clica Search, digita "Blacksmith"
3. Clica no resultado
4. Loop: polling de posicao do char ate chegar perto de (365, 1093)
5. Aguarda 3s pro char parar definitivamente
6. Pronto pra reset_camera e proximos passos
"""
import time
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.lib.math import linear_distance

BLACKSMITH_LOCATION = (365, 1093)
ARRIVAL_THRESHOLD = 2          # unidades pra considerar "chegou"
MAX_WAIT_SECONDS = 60          # timeout total
STATIONARY_TIMEOUT_S = 5       # se ficar parado X seg sem chegar, aborta

proc = next(iter(PymemProcess.list_clients()), None)
if proc is None:
    raise SystemExit("client.exe nao encontrado")

print(f"PID={proc.process_id}")
client = Win32ClientWindow(proc)
print(f"Window: {client.get_window_size()}")
print(f"Char esta em: {client.location}")
print(f"Alvo: Blacksmith em {BLACKSMITH_LOCATION}")
print()
print("Comecando em 3s...")
time.sleep(3)

# Passos 1-3: navega ate o Blacksmith
client.search_surroundings("Blacksmith")
time.sleep(1)
client.goto_first_surrounding_result()

# Passo 4: polling ate chegar
print()
print(f"Aguardando chegar perto de {BLACKSMITH_LOCATION} (threshold {ARRIVAL_THRESHOLD})...")
t0 = time.time()
last_loc = None
stationary_t = None
arrived = False

while time.time() - t0 < MAX_WAIT_SECONDS:
    cur_loc = client.location
    dist = linear_distance(cur_loc, BLACKSMITH_LOCATION)
    print(f"  loc={cur_loc}  dist_ate_blacksmith={dist:.1f}")

    if dist < ARRIVAL_THRESHOLD:
        print(f"  >>> CHEGOU! dist={dist:.1f} < {ARRIVAL_THRESHOLD}")
        arrived = True
        break

    # detecta se ficou parado
    if last_loc is not None and linear_distance(cur_loc, last_loc) < 1:
        if stationary_t is None:
            stationary_t = time.time()
        elif time.time() - stationary_t > STATIONARY_TIMEOUT_S:
            print(f"  >>> PAROU sem chegar (dist={dist:.1f}) -- {STATIONARY_TIMEOUT_S}s sem mover. Abortando.")
            break
    else:
        stationary_t = None

    last_loc = cur_loc
    time.sleep(1)
else:
    print(f"  >>> TIMEOUT depois de {MAX_WAIT_SECONDS}s")

# Passo 5: aguarda 3s pro char parar definitivamente
if arrived:
    print()
    print("Aguardando 3s pro char parar definitivamente...")
    time.sleep(3)
    print(f"Char final em: {client.location}")
    print()
    print("Resetando camera (clicando no botao view_reset)...")
    client.reset_camera()
    time.sleep(1)
    print("Camera resetada. Clicando no NPC (centro da tela)...")
    client.click_npc()
    print("Aguardando 1s pro dialog do NPC abrir...")
    time.sleep(1)
    print("Clicando no botao Sell do dialog...")
    client.click_npc_sell_button()
    print(">>> Pronto. Verifica se abriu a janela de venda.")
else:
    print(">>> NAO CHEGOU. Verifica se o coord do Blacksmith e o caminho estavam corretos.")
