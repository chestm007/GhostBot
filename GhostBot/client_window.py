import math
import time
from operator import mul, add

import pymem
import win32api
import win32gui
import win32process

from GhostBot import logger
from GhostBot.lib import vk_codes, win32messages
from GhostBot.lib.math import position_difference
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
        self.proc = pymem.Pymem(proc.th32ProcessID)
        self.char = self.proc.read_int(self.char_addr)
        self._name = None
        self._max_hp = 0
        self._active = False
        self._window_handle = None
        self._set_window_name()
        self._target_name_offsets = None

    @property
    def window_handle(self):
        if self._window_handle is None:
            hwnds = get_hwnds_for_pid(self.proc.process_id)
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

    def press_key(self, key):
        win32gui.SendMessage(self.window_handle, win32messages.WM_KEYDOWN, key)
        time.sleep(0.2)
        win32gui.SendMessage(self.window_handle, win32messages.WM_KEYUP, key)
        time.sleep(0.2)
        return self

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
        pos_diff_mm_pix = map(mul, pos_diff, (-1.6, 1.6))  # corrected to represent 1 pixel per meter
        minimap_pos = tuple(map(math.ceil, map(add, UI_locations.minimap_centre, pos_diff_mm_pix)))  # mouse position
                                                                                                     # relative to minimap center
        self.right_click(minimap_pos)

    @property
    def hp(self):
        hp = self.proc.read_int(self.char + 0x320)
        if hp > self._max_hp:
            self._max_hp = hp
        return hp

    @property
    def max_hp(self):
        """
        this is a hack, we should calculate instead
        """
        return self._max_hp

    @property
    def max_mana(self):
        """
        this reads base mana before pet buffs
        """
        return self.proc.read_int(self.char + 0x2B4)

    @property
    def mana(self):
        return self.proc.read_int(self.char + 0x324)

    @property
    def name(self):
        """
        Character name
        """
        if self._name is None:
            try:
                name = self.proc.read_string(self.char + 0x3C4, byte=16)
            except UnicodeDecodeError:
                return None
            self._name = name
        return self._name

    @property
    def level(self):
        """
        Character Level
        """
        return self.proc.read_short(self.char + 0x32C)

    @property
    def sitting(self):
        """
        200 if sitting, 100 otherwise
        :return: `True` if char sitting, `False` if not
        """
        val = self.proc.read_int(self.base_addr + 0xD450EC)
        return self.proc.read_int(val + 0x290) == 200

    @property
    def in_battle(self):
        """
        boolean value, `True` if in battle, `False` otherwise
        :return:
        """
        val = self.proc.read_int(self.base_addr + 0xD450EC)
        return self.proc.read_bool(val + 0x854)

    @property
    def location_x(self):
        """
        character location * 20, usually also off by .5
        :returns character location as it appears in game
        """
        return self.proc.read_float(self.char + 0x778) / 20

    @property
    def location_y(self):
        """
        character location * 20, usually also off by .5
        :returns character location as it appears in game
        """
        return self.proc.read_float(self.char + 0x77C) / 20

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
            value = self._read_with_offsets(
                    [self.base_addr + 0xECE2E0, 0x18, 0x1BDC, 0x0, 0xC, 0x1F8, 0x448, 0xC00],
                    self.proc.read_int)
            return math.ceil((value - TARGET_MIN_HP) / (TARGET_MAX_HP - TARGET_MIN_HP) * 100) if value >= TARGET_MIN_HP else -1
        except pymem.exception.MemoryReadError as e:
            logger.error(e)

    @property
    def target_name(self):
        if self._target_name_offsets is not None:  # If we've already saved the right offset, use that
            return self._read_with_offsets(self._target_name_offsets, self.proc.read_string, byte=32)

        self._target_name_offsets = [self.base_addr + 0xECE2E0, 0x18, 0xB1C, 0x0, 0xC, 0xD9C, 0x9AC]
        target_name = self._read_with_offsets(self._target_name_offsets, self.proc.read_string, byte=32)
        if  target_name and target_name.replace(' ', '').isalnum():
            return target_name
        else:  # if its jibberish try the second location
            self._target_name_offsets.append(0x0)
            target_name = self._read_with_offsets(self._target_name_offsets, self.proc.read_string, byte=32)
            if target_name and target_name.replace(' ', '').isalnum():
                return target_name

        # if we get here, its because bot addresses didnt read the right target name
        self._target_name_offsets = None
        raise Exception(f'target name not found for {self.name}: found {target_name}')

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
