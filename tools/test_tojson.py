"""Chama to_json() direto no client pra ver se crasha ou o que retorna."""
import traceback

from GhostBot.controller.bot_controller import BotClientWindow
from GhostBot.lib.tooling import get_client

try:
    c = BotClientWindow(get_client().proc)
    print("BotClientWindow criado. name =", repr(c.name))
    d = c.to_json()
    print("to_json OK:")
    for k, v in d.items():
        print(f"  {k} = {v!r}")
except Exception:
    print("=== EXCECAO em to_json ===")
    traceback.print_exc()
