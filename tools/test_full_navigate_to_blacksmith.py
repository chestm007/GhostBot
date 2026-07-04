"""
Test the full flow to navigate to the Blacksmith:

1. Open Surroundings (window-aware formula)
2. Click the Search button (fixed top-left coord)
3. Type "Blacksmith"
4. Click the first result (fixed top-left coord)

PRE-CONDITIONS:
- Surroundings panel is closed OR open in the upper-left corner
- There is an NPC called Blacksmith nearby (or another name with Blacksmith)
"""
import time

from GhostBot.lib.tooling import get_client

client = get_client()
print(f"Window: {client.get_window_size()}")
print()
print("Starting full flow in 3s...")
time.sleep(3)

# Step 1+2+3: open surroundings, click search, type Blacksmith
client.search_surroundings("Blacksmith")

# Wait 1s for the result to appear
print("Waiting 1s for the result to appear...")
time.sleep(1)

# Step 4: click the first result (Blacksmith)
client.goto_first_surrounding_result()

print()
print("Done. Check:")
print("  - Panel opened?")
print("  - Search clicked and Blacksmith typed?")
print("  - Clicked on Blacksmith in the list?")
print("  - Is the char walking to the Blacksmith?")
