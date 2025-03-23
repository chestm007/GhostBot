import math
import time
from ctypes import windll
from ctypes.wintypes import LPARAM
from operator import mul, add

import pymem
import win32api
import win32gui
import win32process
import win32ui
from pymem.exception import MemoryReadError, ProcessError

from GhostBot import logger
from GhostBot.lib import vk_codes, win32messages
from GhostBot.lib.math import position_difference, limit
from GhostBot.lib.talisman_online_python.pointers import Pointers
from GhostBot.lib.talisman_ui_locations import UI_locations

TARGET_MAX_HP=597
TARGET_MIN_HP=461

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
    base_addr = 0x400000
    char_addr = base_addr + 0xC20980

    def __init__(self, proc):
        self.process_id = proc.th32ProcessID
        self.proc = pymem.Pymem(self.process_id)
        try:
            self.pointers = Pointers(self.process_id)
            self.char = self.proc.read_int(self.char_addr)
        except (ProcessError, MemoryReadError):
            self.pointers = None  # TODO: set this when client login

        self._name = None
        self._active = False
        self._window_handle = None
        self._set_window_name()
        self._target_name_offsets = None

    @property
    def window_handle(self):
        if self._window_handle is None:
            hwnds = get_hwnds_for_pid(self.process_id)
            if len(hwnds) == 1:
                self._window_handle = hwnds[0]
        return self._window_handle

    def _set_window_name(self):
        if self.name is not None:
            win32gui.SetWindowText(self.window_handle, f'Talisman Online | {self.name}')
        return self

    def new_target(self):
        self.press_key(vk_codes['tab'])
        return self

    def target_self(self):
        self.press_key(vk_codes['F1'])
        return self

    def sit(self):
        self.press_key(vk_codes['x'])
        return self

    def capture_screen(self):

        left, top, right, bot = win32gui.GetWindowRect(self._window_handle)
        w = right - left
        h = bot - top

        handle_dc = win32gui.GetWindowDC(self._window_handle)
        mfc_dc = win32ui.CreateDCFromHandle(handle_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        save_bit_map = win32ui.CreateBitmap()
        save_bit_map.CreateCompatibleBitmap(mfc_dc, w, h)

        save_dc.SelectObject(save_bit_map)

        # Change the line below depending on whether you want the whole window
        # or just the client area.
        # result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 1)
        result = windll.user32.PrintWindow(self._window_handle, save_dc.GetSafeHdc(), 1)
        print(result)

        bmpinfo = save_bit_map.GetInfo()
        bmpstr = save_bit_map.GetBitmapBits(True)

        from PIL import Image

        im = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)

        win32gui.DeleteObject(save_bit_map.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(self._window_handle, handle_dc)

        if result == 1:
            # PrintWindow Succeeded
            im.save("test.png")


    def press_key(self, key):
        _key = vk_codes[key.lower()] - 0x20 if key.isupper() else vk_codes[key.lower()]
        #if key.isupper():
        #    print(win32gui.SendMessage(self.window_handle, win32messages.WM_KEYDOWN, vk_codes['left_shift'], LPARAM(0)))

        win32gui.SendMessage(self.window_handle, win32messages.WM_CHAR, _key, LPARAM(0))

        #if key.isupper():
        #    print(win32gui.SendMessage(self.window_handle, win32messages.WM_KEYUP, vk_codes['left_shift'], LPARAM(0)))
        #    time.sleep(0.2)
        return


    def _press_key(self, key):
        if key.isupper():
            print(win32gui.SendMessage(self.window_handle, win32messages.WM_KEYDOWN, vk_codes['left_shift'], LPARAM(0)))

        print(win32gui.SendMessage(self.window_handle, win32messages.WM_CHAR, vk_codes[key.lower()], LPARAM(0)))
        time.sleep(0.1)
        #print(win32gui.SendMessage(self.window_handle, win32messages.WM_KEYUP, vk_codes[key.lower()], LPARAM(0)))
        time.sleep(0.1)
        if key.isupper():
            print(win32gui.SendMessage(self.window_handle, win32messages.WM_KEYUP, vk_codes['left_shift'], LPARAM(0)))
            time.sleep(0.1)
        return self

    def type_keys(self, keys):
        for key in keys:
            self.press_key(key)

    def left_click(self, pos):
        lparam = win32api.MAKELONG(*pos)
        win32gui.SendMessage(self.window_handle, win32messages.WM_MOUSEMOVE, None, lparam)
        win32gui.SendMessage(self.window_handle, win32messages.WM_LBUTTONDOWN, None, lparam)
        win32gui.SendMessage(self.window_handle, win32messages.WM_LBUTTONUP, None, lparam)

    def right_click(self, pos):
        lparam = win32api.MAKELONG(*pos)
        win32gui.SendMessage(self.window_handle, win32messages.WM_MOUSEMOVE, None, lparam)
        win32gui.SendMessage(self.window_handle, win32messages.WM_RBUTTONDOWN, None, lparam)
        win32gui.SendMessage(self.window_handle, win32messages.WM_RBUTTONUP, None, lparam)

    def move_to_pos(self, target_pos):
        """
        moves to `target_pos`
        :param target_pos: `tuple(x, y)` coordinates to move too
        :return:
        """
        xy = (self.location_x, self.location_y)
        pos_diff = position_difference(xy, target_pos)
        pos_diff_mm_pix = tuple(map(mul, pos_diff, (-1.6, 1.6)))  # corrected to represent 1 pixel per meter

        # if diff > 20, we wont have enough pixels
        pos_diff_trimmed = tuple(map(lambda p: limit(p, 20), pos_diff_mm_pix))
        logger.debug(f'raw: {pos_diff_mm_pix} | capped: {pos_diff_trimmed}')
        minimap_pos = tuple(map(math.ceil, map(add, UI_locations.minimap_centre, pos_diff_trimmed)))  # mouse position
        if any(map(lambda p: p > 20, pos_diff_trimmed)):
            logger.error(f'{self.name}: minimap pos too big {pos_diff_trimmed}')
            return

        logger.debug(f'{self.name}: clicking {pos_diff_trimmed}')  # relative to minimap center
        self.right_click(minimap_pos)

    def open_surroundings_ui(self):
        self.left_click(UI_locations.minimap_surroundings)

    def search_surroundings(self, val):
        self.open_surroundings_ui()
        self.left_click(UI_locations.surroundings_search)
        time.sleep(0.2)
        self.type_keys(val)

    def goto_first_surrounding_result(self):
        self.left_click(UI_locations.surroundings_firstitem)
        self.open_surroundings_ui()


    @property
    def hp(self):
        return self.pointers.get_hp()

    @property
    def max_hp(self):
        """
        this is a hack, we should calculate instead
        """
        return self.pointers.get_max_hp()

    @property
    def max_mana(self):
        """
        this reads base mana before pet buffs
        """
        return self.pointers.get_max_mana()

    @property
    def mana(self):
        return self.pointers.get_mana()

    @property
    def name(self):
        """
        Character name
        """
        if self._name is None:
            try:
                name = self.proc.read_string(self.char + 0x3C4, byte=16)
            except UnicodeDecodeError:
                name = self.pointers.get_char_name()
            except (MemoryReadError, AttributeError):
                return None
            self._name = name
        return self._name

    @property
    def level(self):
        """
        Character Level
        """
        return self.pointers.get_level()

    @property
    def sitting(self):
        """
        200 if sitting, 100 otherwise
        :return: `True` if char sitting, `False` if not
        """
        return self.pointers.is_sitting()

    @property
    def in_battle(self):
        """
        boolean value, `True` if in battle, `False` otherwise
        :return:
        """
        return self.pointers.is_in_battle() or False

    @property
    def location_x(self):
        """
        character location * 20, usually also off by .5
        :returns character location as it appears in game
        """
        return self.pointers.get_x()

    @property
    def location_y(self):
        """
        character location * 20, usually also off by .5
        :returns character location as it appears in game
        """
        return self.pointers.get_y()

    @property
    def location(self):
        """
        convenience method to return a tuple of our location
        """
        return self.location_x, self.location_y

    @property
    def target_hp(self):
        """
        NOT LINEAR
        597 when 100%
        461 when 0%
        0 when dead
        :returns target HP 0-100
        """
        try:
            if self.pointers.is_target_selected():
                value = self.pointers.target_hp()
                return math.ceil((value - TARGET_MIN_HP) / (TARGET_MAX_HP - TARGET_MIN_HP) * 100) if value >= TARGET_MIN_HP else -1
            else:
                return None
        except pymem.exception.MemoryReadError as e:
            logger.error(e)

    @property
    def target_name(self):
        if self.pointers.is_target_selected():
            return self.pointers.get_target_name()
        else:
            return None

    def _read_with_offsets(self, in_offsets, get_func, **kwargs):
        """
        gets the data at the last offset in `in_offsets`
        :param in_offsets: List of offsets to get to the data we want
        :param get_func: should be one of `self.proc.read_x` and is used to read the last offset
        :param kwargs: passed directly into `get_func`
        :return: result of `get_func`
        """
        try:
            offsets = list(in_offsets)
            var = 0
            last = offsets.pop()
            for offset in offsets:
                var = self.proc.read_int(var + offset)
            return get_func(var + last, **kwargs)
        except UnicodeDecodeError as e:
            pass


def main():
    for proc in pymem.process.list_processes():
        if proc.szExeFile == b'client.exe':
            client = ClientWindow(proc)
            print(f'-- {client.name} | {client.level} --  {client.proc.process_id}')
            print(f'HP: {client.hp}')
            print(f'MP: {client.mana}/{client.max_mana}')
            print(f'XY: {client.location_x}/{client.location_y}')
            print(f'THP: {client.target_hp}')
            print(f'Sit: {client.sitting}')
            print(f'Bat: {client.in_battle}')
            print(f'Target_name: {client.target_name}')


if __name__ == "__main__":
    main()
