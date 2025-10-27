import ctypes.wintypes
import logging
import math
import time
from ctypes import windll
from ctypes.wintypes import LPARAM, WPARAM
from operator import mul, add
from typing import NamedTuple

import pymem
import win32.win32api
import win32api
import win32gui
import win32process
import win32ui
from pymem.exception import MemoryReadError, ProcessError
from win32con import SM_CYCAPTION

from GhostBot import logger
from GhostBot.lib import vk_codes, win32messages
from GhostBot.lib.math import position_difference, limit
from GhostBot.lib.talisman_online_python.pointers import Pointers
from GhostBot.lib.talisman_ui_locations import UI_locations
from GhostBot.lib.win32.process import PymemProcess

TARGET_MAX_HP=597
TARGET_MIN_HP=461


def get_pointer(self, base, offsets):
    address = self.read_int(base)
    for offset in offsets:
        address = self.read_int(address + offset)
    return address


def get_hwnds_for_pid(pid):
    def callback(hwnd, _hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                _hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds


pymem.Pymem.get_pointer = get_pointer


class ClientWindow:
    base_addr = 0x400000
    char_addr = base_addr + 0xC20980

    def __init__(self, proc):
        self.proc = proc
        self.process_id = proc.process_id
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
        self.press_key('tab')
        return self

    def target_self(self):
        self.press_key('F1')
        return self

    def sit(self):
        self.press_key('x')
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
        """Fetch the keycode for the key from our map, send it to the client window"""
        try:
            if isinstance(key, str) and len(key) == 1:  # if `key` is [a-zA-Z]
                _key = vk_codes[key.lower()] + 0x20 if key.isupper() else vk_codes[key.lower()]
            else:
                _key = vk_codes[key]
        except AttributeError:
            logger.exception(f'INTERNAL ERROR: {key} not found in vk_codes')
            return
        win32gui.SendMessage(self.window_handle, win32messages.WM_KEYDOWN, _key, LPARAM(0))
        win32gui.SendMessage(self.window_handle, win32messages.WM_KEYUP, _key, LPARAM(0))
        win32gui.SendMessage(self.window_handle, win32messages.WM_CHAR, _key, LPARAM(0))
        return

    def type_keys(self, keys: str):
        for key in keys.swapcase():
            self.press_key(key)
            time.sleep(0.1)

    def left_click(self, pos):
        lparam = win32api.MAKELONG(*pos)
        win32gui.SendMessage(self.window_handle, win32messages.WM_MOUSEMOVE, None, lparam)
        win32gui.SendMessage(self.window_handle, win32messages.WM_LBUTTONDOWN, WPARAM(0x0001), lparam)
        win32gui.SendMessage(self.window_handle, win32messages.WM_LBUTTONUP, None, lparam)

    def right_click(self, pos):
        lparam = win32api.MAKELONG(*pos)
        win32gui.SendMessage(self.window_handle, win32messages.WM_MOUSEMOVE, None, lparam)
        time.sleep(0.1)
        win32gui.SendMessage(self.window_handle, win32messages.WM_RBUTTONDOWN, WPARAM(0x0002), lparam)
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

    @staticmethod
    def get_mouse_window_pos(window_pos: tuple[int, int]) -> tuple[int, int] | None:
        x, y = win32gui.GetCursorPos()

        wx, wy = window_pos
        cursor_pos = (x - wx, y - wy)
        if all(a > 0 for a in cursor_pos):
            return cursor_pos
        return None

    def get_window_size_pos(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        title_bar_height = win32.win32api.GetSystemMetrics(SM_CYCAPTION)
        border_thickness = 8

        wx, wy, ww, wh = win32gui.GetWindowRect(self._window_handle)
        wx += border_thickness
        ww -= border_thickness
        wy += (title_bar_height + border_thickness)
        wh -= border_thickness
        return tuple(((wx, wy), (ww, wh)))

    def get_window_pos(self) -> tuple[int, int]:
        return self.get_window_size_pos()[0]

    def get_window_size(self) -> tuple[int, int]:
        return self.get_window_size_pos()[1]

    def open_surroundings_ui(self):
        self.left_click(UI_locations.minimap_surroundings)

    def search_surroundings(self, val):
        self.open_surroundings_ui()
        self.left_click(UI_locations.surroundings_search)
        time.sleep(0.5)
        self.type_keys(val)

    def goto_first_surrounding_result(self):
        self.left_click(UI_locations.surroundings_firstitem)
        self.open_surroundings_ui()

    def click_npc(self):
        self.right_click(UI_locations.npc_location)

    def reset_camera(self):
        self.left_click(UI_locations.view_reset)

    @property
    def team_size(self) -> int:
        return self.pointers.get_team_size()

    @property
    def team_members(self) -> list[str]:  # TODO: this should return a list of references to ClientWindow
        check = [
            self.pointers.team_name_1,
            self.pointers.team_name_2,
            self.pointers.team_name_3,
            self.pointers.team_name_4,
        ]

        return [check[m]() for m in range(self.team_size - 1)]

    @property
    def inventory_open(self):
        return self.pointers.is_bag_open()

    @property
    def pet_active(self) -> bool:
        """:returns: True if pet is active, False otherwise"""
        return self.pointers.pet_active()

    @property
    def hp(self) -> int:
        """Current HP"""
        return self.pointers.get_hp()

    @property
    def max_hp(self) -> int:
        """Maximum mana"""
        return self.pointers.get_max_hp()

    @property
    def max_mana(self) -> int:
        """Maximum HP"""
        return self.pointers.get_max_mana()

    @property
    def mana(self) -> int:
        return self.pointers.get_mana()

    @property
    def name(self) -> str | None:
        """Character name"""
        if self._name is None:
            try:
                name = self.pointers.get_char_name()
            except UnicodeDecodeError:
                name = self.proc.read_string(self.char + 0x3C4, byte=16)
            except (MemoryReadError, AttributeError):
                return None
            self._name = name
        return self._name

    @property
    def level(self) -> int:
        """Character Level"""
        return self.pointers.get_level()

    @property
    def sitting(self) -> bool:
        """:return: `True` if char sitting, `False` if not"""
        return self.pointers.is_sitting()

    @property
    def in_battle(self) -> bool:
        """boolean value, `True` if in battle, `False` otherwise"""
        return self.pointers.is_in_battle()

    @property
    def location_x(self) -> int:
        """
        character location * 20, usually also off by .5
        :returns character location as it appears in game
        """
        return self.pointers.get_x()

    @property
    def location_y(self) -> int:
        """
        character location * 20, usually also off by .5
        :returns character location as it appears in game
        """
        return self.pointers.get_y()

    @property
    def location(self) -> tuple[int, int]:
        """
        convenience method to return a tuple of our location
        """
        return self.location_x, self.location_y

    @property
    def location_name(self) -> str:
        return self.pointers.get_location() or self.pointers.get_location_2() or None

    @property
    def on_mount(self) -> bool:
        return self.pointers.mount()

    @property
    def target_location(self) -> tuple[int, int] | None:
        if self.has_target:
            x, y, pointer = self.pointers.search_id()
            if x and y:
                return x, y
        return None

    @property
    def target_id(self) -> str:
        return self.pointers.get_target_id()

    @property
    def notification(self) -> bool:
        return self.pointers.get_notification()

    @property
    def has_target(self):
        return self.pointers.is_target_selected()

    @property
    def target_hp(self) -> int | None:
        """
        self.pointers.is_target_selected() is NOT LINEAR
        597 when 100%
        461 when 0%
        0 when dead
        :returns target HP 0-100, -1 if target dead, None if no target
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
    def target_name(self) -> str | None:
        """:return: target name if target selected, `None` if no target"""
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
    from GhostBot.bot_controller import ExtendedClient

    logger.setLevel(logging.DEBUG)
    for proc in PymemProcess.list_clients():
            client = ExtendedClient(proc)
            if client.name in ('LongJohnson'):
                time.sleep(3)
                print(client.get_mouse_window_pos())
                print(client.name)
                print(client.team_members)
                continue
                from GhostBot.functions import Petfood
                from GhostBot.bot_controller import Config
                client.config = Config(client)
                pf = Petfood(client)
                pf._despawn_pet()
                buff = Buffs(client)
                buff.run()
                continue

if __name__ == "__main__":
    main()
