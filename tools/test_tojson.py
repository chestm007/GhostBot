"""Chama to_json() direto no client pra ver se crasha ou o que retorna."""
import traceback
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.controller.bot_controller import BotClientWindow

proc = next(iter(PymemProcess.list_clients()), None)
if proc is None:
    raise SystemExit("client.exe nao encontrado")
try:
    c = BotClientWindow(proc)
    print("BotClientWindow criado. name =", repr(c.name))
    d = c.to_json()
    print("to_json OK:")
    for k, v in d.items():
        print(f"  {k} = {v!r}")
except Exception:
    print("=== EXCECAO em to_json ===")
    traceback.print_exc()
