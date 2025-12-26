import logging
import math
import time
from contextlib import contextmanager
from ctypes.wintypes import LPARAM, WPARAM
from operator import mul, add

import cv2
import numpy as np
import pymem
import win32.win32api
import win32api
import win32con
import win32gui
import win32process
import win32ui
from pymem.exception import MemoryReadError, ProcessError
from win32con import SM_CYCAPTION

from GhostBot import logger
from GhostBot.enums.bot_status import BotStatus
from GhostBot.lib import vk_codes, win32messages
from GhostBot.lib.math import position_difference, limit, coords_to_map_screen_pos, linear_distance, \
    scale_minimap_move_distance
from GhostBot.lib.talisman_online_python.pointers import Pointers
from GhostBot.lib.talisman_ui_locations import UI_locations
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.map_navigation import location_to_zone_map, zones

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
        self._target_name_offsets = None
        try:
            self._set_window_name()
        except TypeError:
            pass
        # FIXME: wrap all getters in a retry DC check loop

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

    @property
    def disconnected(self):
        return bool(self.pointers.get_dc())

    @property
    def on_mount(self) -> bool:
        return self.pointers.mount()

    @contextmanager
    def mounted(self, _key=0):
        yield self.mount(_key)
        self.dismount(_key)

    def mount(self, _key=0):
        attempts = 0
        while not self.on_mount and attempts < 3:
            attempts += 1
            self.press_key(_key)
            time.sleep(4)
        if attempts == 3:
            logger.error("Failed to mount up")

    def dismount(self, _key=0):
        attempts = 0
        while self.on_mount and attempts < 3:
            attempts += 1
            self.press_key(_key)
            time.sleep(4)
        if attempts == 3:
            logger.error("Failed to dismount")

    def capture_window(self, color=False):

        try:
            w, h = self.get_window_size()

            handle_dc = win32gui.GetWindowDC(self._window_handle)
            mfc_dc = win32ui.CreateDCFromHandle(handle_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
            save_dc.SelectObject(save_bitmap)

            save_dc.BitBlt((0, 0), (w, h), mfc_dc, (0, 0), win32con.SRCCOPY)

            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype=np.uint8)
            img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)

            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(self._window_handle, handle_dc)
            win32gui.DeleteObject(save_bitmap.GetHandle())
            if color:
                return img[..., :3]
            else:
                return cv2.cvtColor(img[..., :3], cv2.COLOR_BGR2GRAY)

        except Exception as e:
            print(e)
            return None

    def press_key(self, key: int | str):
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
        time.sleep(0.1)
        win32gui.SendMessage(self.window_handle, win32messages.WM_LBUTTONDOWN, WPARAM(0x0001), lparam)
        win32gui.SendMessage(self.window_handle, win32messages.WM_LBUTTONUP, None, lparam)
        time.sleep(0.1)

    def right_click(self, pos):
        lparam = win32api.MAKELONG(*pos)
        win32gui.SendMessage(self.window_handle, win32messages.WM_MOUSEMOVE, None, lparam)
        time.sleep(0.1)
        win32gui.SendMessage(self.window_handle, win32messages.WM_RBUTTONDOWN, WPARAM(0x0002), lparam)
        win32gui.SendMessage(self.window_handle, win32messages.WM_RBUTTONUP, None, lparam)
        time.sleep(0.1)

    def move_to_pos(self, target_pos):
        """
        moves to `target_pos`, will invoke map based pathing if distance is too far.
        :param target_pos: `tuple(x, y)` coordinates to move too
        """
        while linear_distance(self.location, target_pos) > 50 and self.running:
            logger.debug(f"{self.name} moving via map")
            return self._move_to_pos_via_map(target_pos)

        pos_diff = position_difference(self.location, target_pos)

        pos_diff_mm_pix = tuple(map(mul, pos_diff, (-1.7, 1.7)))  # corrected to represent 1 pixel per meter

        minimap_relative_pos = scale_minimap_move_distance(pos_diff_mm_pix)
        minimap_pos = tuple(map(math.ceil, map(add, UI_locations.minimap_centre, minimap_relative_pos)))  # mouse position

        logger.debug(f'{self.name}: clicking {minimap_relative_pos}')  # relative to minimap center
        self.right_click(minimap_pos)
        self.block_while_moving()

    def _move_to_pos_via_map(self, target_pos: tuple[int, int]):
        zone = location_to_zone_map[self.location_name.strip()]
        screen_coords = coords_to_map_screen_pos(
            zones[zone],
            target_pos
        )
        # Open the map, and try a list of position offsets, starting at the exact point we want to go to
        # this avoids movement being blocked when team members are already where we want to be
        offsets = ((0, 0), (20, 0), (-20, 0), (20, 20), (-20, 20), (-20, -20), (0, -20), (-20, 20), (0, 20))
        self.press_key('m')
        time.sleep(1)
        _loc = self.location
        self.right_click(tuple(map(add, screen_coords, (-30, -30)))) # Click away from tgt to clear possible existing tgt
        for offset in offsets:
            path_tgt = tuple(map(add, screen_coords, offset))
            self.right_click(path_tgt)
            time.sleep(2)
            if linear_distance(_loc, self.location) > 1:
                # If we've started moving, we can stop trying offsets
                break
        else:
            logger.info(f'{self.name}: failed pathing via map')
            self.press_key('m')
            return False

        time.sleep(1)
        self.press_key('m')
        self.block_while_moving(path_tgt)
        if target_pos != path_tgt:
            # If we moved to a non-zero offset location, we will need to use the minimap to move to the right spot
            # we're close enough now that it'll work.
            self.move_to_pos(target_pos)
            self.block_while_moving()
        return True

    def block_while_moving(self, destination=None):
        while self.running:
            _location = self.location
            time.sleep(3)
            if destination is not None:
                if linear_distance(destination, self.location) < 40:  # if we're close enough, no point overshooting.
                    break
            if linear_distance(self.location, _location) < 1:
                break

    @staticmethod
    def get_mouse_window_pos(window_pos: tuple[int, int]) -> tuple[int, int] | None:
        """Get cursor position relative to window position"""
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
        ww -= border_thickness + wx
        wy += (title_bar_height + border_thickness)
        wh -= border_thickness + wy
        return tuple(((wx, wy), (ww, wh)))

    def get_window_pos(self) -> tuple[int, int]:
        return self.get_window_size_pos()[0]

    def get_window_size(self) -> tuple[int, int]:
        return self.get_window_size_pos()[1]

    def open_surroundings_ui(self):
        self.left_click(UI_locations.minimap_surroundings)
        time.sleep(0.5)

    @property
    def inventory_open(self):
        return self.pointers.is_bag_open()

    @contextmanager
    def inventory(self):
        yield self.open_inventory()
        self.close_inventory()

    def open_inventory(self):
        while not self.inventory_open:
            self.press_key('i')
            time.sleep(1)

    def close_inventory(self):
        while self.inventory_open:
            self.press_key('i')
            time.sleep(1)

    def search_surroundings(self, val):
        self.open_surroundings_ui()
        self.left_click(UI_locations.surroundings_search)
        time.sleep(0.5)
        self.type_keys(val)
        time.sleep(0.5)

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
    def location_name(self) -> str | None:
        loc = None
        for loc_pointer in (self.pointers.get_location, self.pointers.get_location_2):
            try:
                if loc_pointer().replace(' ','').replace("'", '').isalpha():
                    if (loc := loc_pointer().strip()) in location_to_zone_map.keys():
                        if loc in location_to_zone_map.keys():
                            return loc
            except AttributeError:
                continue
        return loc

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
        return self.pointers.get_target_name()

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

    #logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.INFO)
    for proc in PymemProcess.list_clients():
        client = ExtendedClient(proc)
        #if client.name == 'LongJohnson':
        if client.has_target:
            print(client.name, client.target_name, client.target_id)
            if client.has_target:
                print(client.target_location)


if __name__ == "__main__":
    main()
