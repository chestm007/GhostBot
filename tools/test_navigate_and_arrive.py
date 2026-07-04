"""
Test the full flow + confirmed arrival at the Blacksmith:

1. Open Surroundings
2. Click Search, type "Blacksmith"
3. Click the result
4. Loop: char position polling until arriving near (365, 1093)
5. Wait 3s for the char to stop permanently
6. Ready for reset_camera and next steps
"""
import time

from GhostBot.lib.math import linear_distance
from GhostBot.lib.tooling import get_client

BLACKSMITH_LOCATION = (365, 1093)
ARRIVAL_THRESHOLD = 2          # units to consider "arrived"
MAX_WAIT_SECONDS = 60          # timeout total
STATIONARY_TIMEOUT_S = 5       # if stationary X sec without arriving, abort

client = get_client()
print(f"Window: {client.get_window_size()}")
print(f"Char is at: {client.location}")
print(f"Target: Blacksmith at {BLACKSMITH_LOCATION}")
print()
print("Starting in 3s...")
time.sleep(3)

# Steps 1-3: navigate to the Blacksmith
client.search_surroundings("Blacksmith")
time.sleep(1)
client.goto_first_surrounding_result()

# Step 4: polling until arrival
print()
print(f"Waiting to arrive near {BLACKSMITH_LOCATION} (threshold {ARRIVAL_THRESHOLD})...")
t0 = time.time()
last_loc = None
stationary_t = None
arrived = False

while time.time() - t0 < MAX_WAIT_SECONDS:
    cur_loc = client.location
    dist = linear_distance(cur_loc, BLACKSMITH_LOCATION)
    print(f"  loc={cur_loc}  dist_ate_blacksmith={dist:.1f}")

    if dist < ARRIVAL_THRESHOLD:
        print(f"  >>> ARRIVED! dist={dist:.1f} < {ARRIVAL_THRESHOLD}")
        arrived = True
        break

    # detect if stationary
    if last_loc is not None and linear_distance(cur_loc, last_loc) < 1:
        if stationary_t is None:
            stationary_t = time.time()
        elif time.time() - stationary_t > STATIONARY_TIMEOUT_S:
            print(f"  >>> STOPPED without arriving (dist={dist:.1f}) -- {STATIONARY_TIMEOUT_S}s without moving. Aborting.")
            break
    else:
        stationary_t = None

    last_loc = cur_loc
    time.sleep(1)
else:
    print(f"  >>> TIMEOUT after {MAX_WAIT_SECONDS}s")

# Step 5: wait 3s for the char to stop permanently
if arrived:
    print()
    print("Waiting 3s for the char to stop permanently...")
    time.sleep(3)
    print(f"Final char at: {client.location}")
    print()
    print("Resetting camera (clicking the view_reset button)...")
    client.reset_camera()
    time.sleep(1)
    print("Camera reset. Clicking on the NPC (center of screen)...")
    client.click_npc()
    print("Waiting 1s for the NPC dialog to open...")
    time.sleep(1)
    print("Clicking the Sell button in the dialog...")
    client.click_npc_sell_button()
    print(">>> Done. Check if the sell window opened.")
else:
    print(">>> DID NOT ARRIVE. Check if the Blacksmith coord and path were correct.")
