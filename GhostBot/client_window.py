import pymem
import win32gui
import win32process

from GhostBot import logger


def get_pointer(self, base, offsets):
    address = self.read_int(base)
    for offset in offsets:
        address = self.read_int(address + offset)
    return address


def get_hwnds_for_pid(pid):
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds


pymem.Pymem.get_pointer = get_pointer


class ClientWindow:
    base_addr = 0x00400000
    char_addr = base_addr + 0x00C20980

    def __init__(self, proc):
        self.proc = pymem.Pymem(proc.th32ProcessID)
        self.char = self.proc.read_int(self.char_addr)
        self._name = None
        self._active = False
        self._set_window_name()

    @property
    def window_handle(self):
        hwnds = get_hwnds_for_pid(self.proc.process_id)
        if len(hwnds) == 1:
            return hwnds[0]

    def _set_window_name(self):
        if self.name is not None:
            win32gui.SetWindowText(self.window_handle, f'Talisman Online | {self.name}')

    @property
    def hp(self):
        return self.proc.read_int(self.char + 0x320)

    @property
    def max_mana(self):
         return self.proc.read_int(self.char + 0x2B4)

    @property
    def mana(self):
        return self.proc.read_int(self.char + 0x324)

    @property
    def name(self):
        if self._name is None:
            self._name = self.proc.read_string(self.char + 0x3C4, byte=16)
        return self._name

    @property
    def level(self):
        return self.proc.read_short(self.char + 0x32C)

    @property
    def location(self):
        return self.proc.read_float(self.char + 0x778) / 20, self.proc.read_float(self.char + 0x77C) / 20

    @property
    def target_hp(self):
        try:
            value = self.proc.read_int(self.base_addr + 0x00ECE2E0)
            for offset in [0x18, 0x1BDC, 0x0, 0xC, 0x1F8, 0x448, 0xC00]:
                value = self.proc.read_int(value + offset)
            return value
        except pymem.exception.MemoryReadError as e:
            logger.error(e)


def main():
    for proc in pymem.process.list_processes():
        if proc.szExeFile == b'client.exe':
            client = ClientWindow(proc)
            print(f'-- {client.name} | {client.level} --  {client.proc.process_id}')
            print(f'HP: {client.hp}')
            print(f'MP: {client.mana}/{client.max_mana}')
            print(f'XY: {client.location}')
            print(f'THP: {client.target_hp}')


if __name__ == "__main__":
    main()
