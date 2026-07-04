"""
Test of the return to spot via map:
  1. Find the open map's "Map" title via template (anchor)
  2. right-click on the spot = title + offset
  3. close the map (M key)
  4. poll location to confirm the char moved

Map needs to be OPEN before running. Does NOT modify production code.
The offset here is a TEST point -- the real one will be chosen by the user in the UI.
"""
import time

import cv2

from GhostBot.lib.math import linear_distance
from GhostBot.lib.tooling import get_client, match_template

MAP_TITLE_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\map_title.bmp"
MAP_TO_SPOT = (-125, 297)   # "Map" title -> farm spot (TEST; real comes from UI)
MAP_DUMMY_OFFSET = (60, 0)  # bait click: spot + this -> different region (fixes the bug
                            # where the game ignores 2 consecutive clicks to the SAME destination)
SPOT_WORLD = (321, 1147)    # world coords of the example spot (read after round 1).
                            # IN PRODUCTION: read client.location at the moment the user
                            # defines the spot (they're farming there) and save it with the offset.
ARRIVAL = 3                 # distance to consider "arrived at spot"
THRESHOLD = 0.70


def main():
    client = get_client()
    print(f"Window: {client.get_window_size()}")

    try:
        title_match = match_template(client, MAP_TITLE_BMP, threshold=THRESHOLD)
        title, score = title_match.center, title_match.score
    except SystemExit:
        title, score = None, 0.0
    if title is None:
        raise SystemExit(f">>> 'Map' title not found (score {score:.3f}). Is the map OPEN?")
    spot = (title[0] + MAP_TO_SPOT[0], title[1] + MAP_TO_SPOT[1])
    dummy = (spot[0] + MAP_DUMMY_OFFSET[0], spot[1] + MAP_DUMMY_OFFSET[1])
    print(f"'Map' title at {title} (score {score:.3f}) -> spot at {spot} | bait at {dummy}")

    start = client.location
    d0 = linear_distance(start, SPOT_WORLD)
    print(f"Char starts at {start} (distance to spot {d0:.1f})")
    if d0 < ARRIVAL:
        print(">>> WARNING: char is already at the spot -- move away first to see the return.")
    # bait click in a different region, then the real spot -> avoid the game bug
    print("BAIT right-click, then SPOT, and close map (M)...")
    client.right_click(dummy)
    time.sleep(0.5)
    client.right_click(spot)
    time.sleep(0.5)
    client.press_key('m')   # close the map to allow movement

    # arrival timer: wait for the char to arrive near the spot (same as Blacksmith)
    t0 = time.time()
    last = None
    stationary_t = None
    arrived = False
    while time.time() - t0 < 45:
        cur = client.location
        d = linear_distance(cur, SPOT_WORLD)
        print(f"  loc={cur}  distance_to_spot={d:.1f}")
        if d < ARRIVAL:
            arrived = True
            print(f"  >>> ARRIVED AT THE SPOT! dist={d:.1f}")
            break
        if last is not None and linear_distance(cur, last) < 1:
            if stationary_t is None:
                stationary_t = time.time()
            elif time.time() - stationary_t > 4:
                print(f"  >>> stopped without arriving (dist={d:.1f})")
                break
        else:
            stationary_t = None
        last = cur
        time.sleep(1)
    else:
        print("  >>> TIMEOUT")

    print("ARRIVED AT THE SPOT" if arrived else "DID NOT ARRIVE")


if __name__ == "__main__":
    main()
