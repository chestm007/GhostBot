"""
Isolated test: open the Surroundings panel + click the Search button + type 'Blacksmith'.

You must keep the Surroundings panel in the UPPER LEFT corner of the TO window.
"""
import time

from GhostBot.lib.tooling import get_client

client = get_client()
ww, wh = client.get_window_size()
print(f"Window: {ww} x {wh}")
print()
print("Going to open surroundings + click search + type 'Blacksmith' in 3s...")
print("REMEMBER: Surroundings panel must be in the UPPER LEFT corner.")
time.sleep(3)

client.search_surroundings("Blacksmith")
print()
print("Done. Check in-game: did the panel open, click Search, and type Blacksmith?")
