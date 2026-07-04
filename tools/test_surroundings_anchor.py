"""
ROBUST test of surroundings via anchor (template) + offsets.

Same scheme as the NPC sell dialog:
  1. Find the "Surroundings" title on screen via template matching
     (Images/misc/surroundings_title.bmp) -- works in ANY position.
  2. From the title center, calculate:
       - golden search field = title + TITLE_TO_SEARCH
       - 1st result in list  = title + TITLE_TO_FIRST_RESULT
  3. Click the field, type SEARCH_TERM.
  4. (if STOP_AFTER_TYPE=False) click the 1st result and poll
     position until arriving near the target -- proves navigation worked.

DO NOT modify production code. DO NOT sell anything.
"""
import time

import cv2
import numpy as np

from GhostBot.lib.math import linear_distance
from GhostBot.lib.tooling import get_client, match_template

# ---- Config ----
TITLE_BMP = r"C:\Bot\BotTO\src\GhostBot\Images\misc\surroundings_title.bmp"
TITLE_MATCH_THRESHOLD = 0.70
TITLE_TO_SEARCH = (140, 347)        # title -> golden search field (calibrated via cursor)
TITLE_TO_FIRST_RESULT = (-106, 70)  # title -> 1st line of list (calibrated via cursor)
SEARCH_TERM = "Blacksmith"
TARGET_LOCATION = (365, 1093)       # where the Blacksmith is (to confirm navigation)
ARRIVAL_THRESHOLD = 2
MAX_WAIT_SECONDS = 60
STATIONARY_TIMEOUT_S = 6

STOP_AFTER_TYPE = False  # True = only search+type+capture (calibration). False = click result and navigate.


def main():
    client = get_client()
    ww, wh = client.get_window_size()
    print(f"Window: {ww} x {wh}")

    # 1) try to find the title (panel already open?). If not, open and try again.
    try:
        title_match = match_template(client, TITLE_BMP, threshold=TITLE_MATCH_THRESHOLD)
        center, score = title_match.center, title_match.score
    except SystemExit:
        center, score = None, 0.0
    if center is None:
        print(f"Title not found (score {score:.3f}) -- opening surroundings panel...")
        client.open_surroundings_ui()
        time.sleep(1.5)
        try:
            title_match = match_template(client, TITLE_BMP, threshold=TITLE_MATCH_THRESHOLD)
            center, score = title_match.center, title_match.score
        except SystemExit:
            center, score = None, 0.0
    if center is None:
        raise SystemExit(f">>> FAILED: title not found even after opening (score {score:.3f})")
    print(f"'Surroundings' title found at {center}  (score {score:.3f})")

    search_pos = (center[0] + TITLE_TO_SEARCH[0], center[1] + TITLE_TO_SEARCH[1])
    result_pos = (center[0] + TITLE_TO_FIRST_RESULT[0], center[1] + TITLE_TO_FIRST_RESULT[1])
    print(f"Search field calculated: {search_pos}")
    print(f"1st result calculated:   {result_pos}")

    # 2) click the field and type
    print(f"Clicking the search field and typing '{SEARCH_TERM}'...")
    client.left_click(search_pos)
    time.sleep(0.5)
    for _ in range(15):                 # clear any previous text in the field
        client.press_key('backspace')
    time.sleep(0.3)
    client.type_keys(SEARCH_TERM)
    time.sleep(1.0)

    # 3) capture for review
    out = r"C:\Bot\BotTO\tmp_after_search.png"
    cv2.imwrite(out, client.capture_window(color=True))
    print(f"Post-search screenshot saved to {out}")

    if STOP_AFTER_TYPE:
        print(">>> STOP_AFTER_TYPE=True: stopping here to review the screenshot.")
        return

    # 4) click the result and confirm navigation
    print(f"Clicking the 1st result at {result_pos}...")
    client.left_click(result_pos)

    t0 = time.time()
    last_loc = None
    stationary_t = None
    arrived = False
    while time.time() - t0 < MAX_WAIT_SECONDS:
        cur = client.location
        dist = linear_distance(cur, TARGET_LOCATION)
        print(f"  loc={cur}  dist={dist:.1f}")
        if dist < ARRIVAL_THRESHOLD:
            print(f"  >>> CHEGOU! dist={dist:.1f}")
            arrived = True
            break
        if last_loc is not None and linear_distance(cur, last_loc) < 1:
            if stationary_t is None:
                stationary_t = time.time()
            elif time.time() - stationary_t > STATIONARY_TIMEOUT_S:
                print(f"  >>> STOPPED without arriving (dist={dist:.1f}). Aborting.")
                break
        else:
            stationary_t = None
        last_loc = cur
        time.sleep(1)
    else:
        print(f"  >>> TIMEOUT {MAX_WAIT_SECONDS}s")

    print("ARRIVED" if arrived else "DID NOT ARRIVE")

    # 5) close the surroundings panel (second click on the minimap eye)
    if arrived:
        print("Closing surroundings panel (2nd click on the minimap eye)...")
        client.open_surroundings_ui()   # open_surroundings_ui = toggle of the eye


if __name__ == "__main__":
    main()
