"""
Open the NPC window (assuming char is already on top of it) to inspect
the "Sell Item" button. Camera reset + right-click center.
DO NOT sell anything -- just open and capture.
"""
import time
import cv2

from GhostBot.lib.tooling import get_client

client = get_client()
print("Window:", client.get_window_size())

print("Resetting camera...")
client.reset_camera()
time.sleep(1.5)

print("Right-click on NPC (center of screen)...")
client.click_npc()
time.sleep(1.5)

out = r"C:\Bot\BotTO\tmp_npc_window.png"
cv2.imwrite(out, client.capture_window(color=True))
print("Screenshot saved:", out)
