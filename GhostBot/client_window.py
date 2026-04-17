import math
import time
from ctypes.wintypes import LPARAM, WPARAM

import cv2
import numpy as np
import pymem
import pywintypes
import win32.win32api
import win32api
import win32con
import win32gui
import win32process
import win32ui

from pymem.exception import MemoryReadError, ProcessError
from win32con import SM_CYCAPTION

from GhostBot.abstract_client_window import AbstractClientWindow, Location
from GhostBot.lib import win32messages, get_with_case
from GhostBot.lib.talisman_online_python.pointers import Pointers
from GhostBot.map_navigation import location_to_zone_map

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


class Win32ClientWindow(AbstractClientWindow):
    """
    Class to interact with the Talisman Online client window under Microsoft Windows.
    """
    base_addr = 0x400000
    char_addr = base_addr + 0xC20980

    def __init__(self, proc):
        super().__init__()
        self._name = None
        self._active = False
        self._window_handle = None
        self._target_name_offsets = None
        self.pointers = None
        self.char = None

        self.proc = proc
        self.process_id = proc.process_id

        self.initialize_pointers()

        try:
            self.set_window_name()
        except TypeError:
            pass
        # FIXME: wrap all getters in a retry DC check loop

    @property
    def identifier(self):
        return f"{self.name or ''}[{self.process_id}]"

    def initialize_pointers(self, force_reload: bool = False):
        try:
            if self.pointers is None or force_reload:
                self.logger.debug('Win32ClientWindow :: %s :: %s initializing pointers', self.identifier, 'FORCE' if force_reload else '')
                self.pointers = Pointers(self.process_id)
            if self.char is None or force_reload:
                self.char = self.proc.read_int(self.char_addr)
        except (ProcessError, MemoryReadError):
            return

    @property
    def window_handle(self):
        if self._window_handle is None:
            hwnds = get_hwnds_for_pid(self.process_id)
            if len(hwnds) == 1:
                self.logger.debug('Win32ClientWindow :: %s :: got window handle', self.identifier)
                self._window_handle = hwnds[0]
        return self._window_handle

    def set_window_name(self):
        if self.name is not None:
            win32gui.SetWindowText(self.window_handle, f'Talisman Online | {self.name}')
        return self

    def get_window_name(self) -> str:
        try:
            return win32gui.GetWindowText(self.window_handle).split(' | ')[-1]
        except IndexError:
            return ''

    @property
    def disconnected(self):
        return bool(self.pointers.get_dc())

    @property
    def on_mount(self) -> bool:
        return self.pointers.mount()

    def capture_window(self, color=False):
        w, h = self.get_window_size()

        handle_dc = win32gui.GetWindowDC(self.window_handle)
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
        win32gui.ReleaseDC(self.window_handle, handle_dc)
        win32gui.DeleteObject(save_bitmap.GetHandle())
        if color:
            return img[..., :3]
        else:
            return cv2.cvtColor(img[..., :3], cv2.COLOR_BGR2GRAY)

    def press_key(self, _key: int | str | None, char_only: bool = False):
        """Send the key to the client window"""
        try:
            __key = get_with_case(_key)
        except AttributeError:
            return

        if not char_only:
            win32gui.SendMessage(self.window_handle, win32messages.WM_KEYDOWN, __key, LPARAM(0))
        win32gui.SendMessage(self.window_handle, win32messages.WM_CHAR, __key, LPARAM(0))
        if not char_only:
            win32gui.SendMessage(self.window_handle, win32messages.WM_KEYUP, __key, LPARAM(0))
        return

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

    def close_window(self):
        win32gui.SendMessage(self._window_handle, win32messages.WM_DESTROY, None, None)

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

        try:
            wx, wy, ww, wh = win32gui.GetWindowRect(self.window_handle)
        except pywintypes.error:
            self.logger.debug('Win32ClientWindow :: %s :: error getting window handle %s', self.identifier, self.window_handle)
            return None
        wx += border_thickness
        ww -= border_thickness + wx
        wy += (title_bar_height + border_thickness)
        wh -= border_thickness + wy
        return (wx, wy), (ww, wh)

    @property
    def inventory_open(self):
        return self.pointers.is_bag_open()

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
        """:return: ``True`` if char sitting, ``False`` if not"""
        return self.pointers.is_sitting()

    @property
    def in_battle(self) -> bool:
        """:return: ``True`` if in battle, ``False`` otherwise"""
        return self.pointers.is_in_battle()

    @property
    def location(self) -> tuple[int, int]:
        """
        convenience method to return a tuple of our location
        """
        return Location(self.pointers.get_x(), self.pointers.get_y())

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
            self.logger.error(e)

    @property
    def target_name(self) -> str | None:
        """:return: target name if target selected, `None` if no target"""
        return self.pointers.get_target_name()
