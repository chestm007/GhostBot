"""
Test different ways to send a click to a coord in the TO window.
Uses the same APIs as the bot.

USAGE:
  python tools\test_click_methods.py            # test all methods
  python tools\test_click_methods.py SENDMSG    # test only SendMessage (same as current bot)
  python tools\test_click_methods.py POSTMSG    # test PostMessage (async)
  python tools\test_click_methods.py INPUT      # test SendInput (hardware simulation)
"""
import sys
import time
import ctypes
from ctypes import wintypes
import win32api
import win32gui
import win32process
import win32con
import pymem

# Coord to click (surroundings button) -- REAL coord where the button is visually
# (measured via where_is_cursor.py, not the template match coord that had 30px offset)
CLICK_X, CLICK_Y = 1551, 60

# Find PID of client.exe
pid = None
for proc in pymem.process.list_processes():
    if proc.szExeFile == b'client.exe':
        pid = proc.th32ProcessID
        break
if pid is None:
    raise SystemExit("client.exe not found")
print(f"client.exe PID={pid}")

# Find window
def enum_callback(hwnd, results):
    _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
    if found_pid == pid and win32gui.IsWindowVisible(hwnd):
        results.append(hwnd)
windows = []
win32gui.EnumWindows(enum_callback, windows)
if not windows:
    raise SystemExit(f"No window found for PID {pid}")
hwnd = windows[0]
print(f"Window handle: {hwnd}")
print(f"Title: {win32gui.GetWindowText(hwnd)}")

# Get client area size
client_rect = win32gui.GetClientRect(hwnd)
print(f"Client rect: {client_rect}  (width={client_rect[2]-client_rect[0]}, height={client_rect[3]-client_rect[1]})")
print(f"Clicking at: ({CLICK_X}, {CLICK_Y})")

method = sys.argv[1].upper() if len(sys.argv) > 1 else 'ALL'

def sendmsg():
    print("\n[SENDMSG] Using win32gui.SendMessage (same as current bot)...")
    lparam = win32api.MAKELONG(CLICK_X, CLICK_Y)
    win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
    time.sleep(0.1)
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
    print("[SENDMSG] sent. Look at the game now -- did surroundings open?")

def postmsg():
    print("\n[POSTMSG] Using win32gui.PostMessage (async)...")
    lparam = win32api.MAKELONG(CLICK_X, CLICK_Y)
    win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
    time.sleep(0.1)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
    print("[POSTMSG] sent. Look at the game.")

def send_input():
    """SendInput simulates hardware click -- more authentic."""
    print("\n[INPUT] Hardware mode -- I'm going to MOVE your cursor and click.")
    print("        TAKE YOUR HAND OFF THE MOUSE now. Starting in 3s...")
    time.sleep(3)

    pt = wintypes.POINT(CLICK_X, CLICK_Y)
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))
    screen_x, screen_y = pt.x, pt.y
    print(f"  client ({CLICK_X},{CLICK_Y}) -> screen ({screen_x},{screen_y})")

    print("  Focusing TO window...")
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"  WARNING: SetForegroundWindow failed: {e}")
    time.sleep(0.5)

    print(f"  Moving cursor to ({screen_x},{screen_y})...")
    win32api.SetCursorPos((screen_x, screen_y))
    time.sleep(0.5)

    actual = win32api.GetCursorPos()
    print(f"  Cursor now at: {actual}")
    if actual != (screen_x, screen_y):
        print(f"  WARNING: cursor DID NOT go to the expected place! SetCursorPos may be blocked.")

    print("  Clicking (mouse_event LBUTTON down + up)...")
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.5)
    print("[INPUT] sent. Look at the game in the next 3 seconds.")
    time.sleep(3)
    print("[INPUT] done. Did surroundings open?")

if method in ('SENDMSG', 'ALL'):
    sendmsg()
    if method == 'ALL':
        time.sleep(3)
        print("\n--- wait 3s, closing surroundings (if it opened, press ESC in-game) ---")
        time.sleep(2)

if method in ('POSTMSG', 'ALL'):
    postmsg()
    if method == 'ALL':
        time.sleep(3)
        print("\n--- wait 3s ---")
        time.sleep(2)

if method in ('INPUT', 'ALL'):
    send_input()

print("\nEnd of test.")
