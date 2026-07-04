"""
Isolated test: open the Surroundings panel via open_surroundings_ui()
of AbstractClientWindow -- just that, nothing else, no bot, no sell, no loop.

Uses the new formula: pos = (window_width - 49, 60)
"""
import time

from GhostBot.lib.tooling import get_client

client = get_client()
ww, wh = client.get_window_size()
print(f"Window size: {ww} x {wh}")
print(f"open_surroundings_ui vai clicar em: ({ww - 49}, 60)")
print()
print("Going to click in 3 seconds... look at the game")
time.sleep(3)

print("Clicking now!")
client.open_surroundings_ui()

print()
print("\nDone. Did the Surroundings panel open?")
