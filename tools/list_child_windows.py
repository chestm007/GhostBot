"""Lista janelas-filho (child windows) do TO."""
import win32gui
import win32process
import pymem

pid = None
for proc in pymem.process.list_processes():
    if proc.szExeFile == b'client.exe':
        pid = proc.th32ProcessID
        break
if pid is None:
    raise SystemExit("client.exe nao encontrado")

def find_top_windows():
    tops = []
    def cb(hwnd, _):
        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
        if found_pid == pid and win32gui.IsWindowVisible(hwnd):
            tops.append(hwnd)
    win32gui.EnumWindows(cb, None)
    return tops

def enum_children(hwnd, depth=0):
    def cb(child_hwnd, _):
        try:
            cls = win32gui.GetClassName(child_hwnd)
            text = win32gui.GetWindowText(child_hwnd)
            rect = win32gui.GetClientRect(child_hwnd)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            print(f"{'  '*(depth+1)}- handle={child_hwnd} class={cls!r} text={text!r} size={w}x{h}")
            enum_children(child_hwnd, depth + 1)
        except Exception as e:
            print(f"{'  '*(depth+1)}- (erro: {e})")
    try:
        win32gui.EnumChildWindows(hwnd, cb, None)
    except Exception:
        pass

for hwnd in find_top_windows():
    cls = win32gui.GetClassName(hwnd)
    text = win32gui.GetWindowText(hwnd)
    rect = win32gui.GetClientRect(hwnd)
    print(f"TOP: handle={hwnd} class={cls!r} text={text!r} size={rect[2]-rect[0]}x{rect[3]-rect[1]}")
    enum_children(hwnd)
