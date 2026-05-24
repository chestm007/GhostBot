"""
Teste do fluxo completo de navegar ate o Blacksmith:

1. Abre Surroundings (formula window-aware)
2. Clica no botao Search (coord fixa top-left)
3. Digita "Blacksmith"
4. Clica no primeiro resultado (coord fixa top-left)

PRE-CONDICOES:
- Painel Surroundings esta fechado OU aberto no canto superior esquerdo
- Existe um NPC chamado Blacksmith proximo (ou outro nome com Blacksmith)
"""
import time
from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess

proc = next(iter(PymemProcess.list_clients()), None)
if proc is None:
    raise SystemExit("client.exe nao encontrado")

print(f"PID={proc.process_id}")
client = Win32ClientWindow(proc)
print(f"Window: {client.get_window_size()}")
print()
print("Comecando fluxo completo em 3s...")
time.sleep(3)

# Passo 1+2+3: abre surroundings, clica search, digita Blacksmith
client.search_surroundings("Blacksmith")

# Espera 1s pro resultado aparecer
print("Aguardando 1s pro resultado aparecer...")
time.sleep(1)

# Passo 4: clica no primeiro resultado (Blacksmith)
client.goto_first_surrounding_result()

print()
print("Done. Verifica:")
print("  - Painel abriu?")
print("  - Search clicou e digitou Blacksmith?")
print("  - Clicou no Blacksmith na lista?")
print("  - O char esta andando ate o Blacksmith?")
