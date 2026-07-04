__all__ = ['AbstractClientWindow']

import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Self

from GhostBot import logger as _logger
from GhostBot.image_finder import ImageFinder
from GhostBot.lib.types import Location
from GhostBot.lib.talisman_ui_locations import UI_locations


class AbstractClientWindow(ABC):
    """
    Abstract Class containing all methods expected to interact with the Talisman Online client window.
    """
    def __init__(self):
        self.logger = _logger.getChild(self.__class__.__name__)
        self._image_finder = ImageFinder(self)

    @property
    @abstractmethod
    def identifier(self) -> str: ...

    @property
    @abstractmethod
    def window_handle(self) -> int: ...

    @abstractmethod
    def set_window_name(self) -> Self: ...

    @property
    def has_alive_target(self):
        try:
            if self.target_hp < 0:
                return False
        except TypeError:
            return False
        if self.target_name == self.name:
            return False
        return True

    def new_target(self, _key='tab') -> Self:
        self.press_key(_key)
        return self

    def sit(self, _key='x') -> Self:
        self.press_key(_key)
        return self

    @property
    @abstractmethod
    def disconnected(self) -> bool: ...

    @abstractmethod
    def on_mount(self) -> bool: ...

    @contextmanager
    def mounted(self, _key=None):
        if _key is None:
            yield
            return

        self.mount(_key)
        yield
        self.dismount(_key)

    def mount(self, _key=None):
        if _key is None:
            return

        attempts = 0
        while not self.on_mount and attempts < 3:
            attempts += 1
            self.press_key(_key)
            time.sleep(4)
        if attempts == 3:
            self.logger.error("Failed to mount up")

    def dismount(self, _key=None):
        if _key is None:
            return

        attempts = 0
        while self.on_mount and attempts < 3:
            attempts += 1
            self.press_key(_key)
            time.sleep(4)
        if attempts == 3:
            self.logger.error("Failed to dismount")

    @abstractmethod
    def capture_window(self, color: bool = False): ...

    @abstractmethod
    def press_key(self, key: int | str, char_only: bool = False) -> None: ...

    def type_keys(self, keys: str, char_only: bool = False) -> None:
        for key in keys.swapcase():
            self.press_key(key, char_only=char_only)

    @abstractmethod
    def left_click(self, pos: tuple[float, float]) -> None: ...

    @abstractmethod
    def right_click(self, pos: tuple[float, float]) -> None: ...

    @staticmethod
    @abstractmethod
    def get_mouse_window_pos(window_pos: tuple[int, int]) -> Location | None: ...

    @abstractmethod
    def get_window_size_pos(self) -> tuple[Location, Location] | None: ...

    def get_window_pos(self) -> Location:
        return self.get_window_size_pos()[0]

    def get_window_size(self) -> Location:
        return self.get_window_size_pos()[1]

    def _resolve_button_pos(self, bmp_name: str, fallback: tuple[int, int],
                            threshold: float = 0.75) -> tuple[int, int]:
        """
        Tries to find a button in the window via template matching of Images/misc/<bmp_name>.
        If not found (BMP missing or match below threshold), returns the hardcoded `fallback`
        coordinate (from UI_locations) -- so the bot keeps working until the user
        captures the BMP.
        """
        pos = self._image_finder.find_button_center(bmp_name, threshold=threshold)
        if pos is None:
            self.logger.info("%s not found by template, using fallback coord %s", bmp_name, fallback)
            return fallback
        self.logger.info("%s found by template at %s", bmp_name, pos)
        return pos

    # ============================================================
    # UI POSITIONS (discovered via find_anchor.py / where_is_cursor.py)
    # ============================================================
    #
    # TO's HUD is "anchored to corners" -- it doesn't scale with window size,
    # it sticks to the corner. For each UI element we know:
    #   - which corner it anchors to
    #   - fixed pixel offset (x, y) from that corner
    #
    # To ADD a new button: run tools/find_anchor.py, position mouse
    # on the button, it tells you which corner and what offset.
    #
    # COORDINATE CONVENTION: CLIENT coord (no title bar, no border).
    # ============================================================

    # Minimap surroundings button (top-right anchor)
    _MINIMAP_SURROUNDINGS_OFFSET_RIGHT = 49
    _MINIMAP_SURROUNDINGS_OFFSET_TOP = 60

    # Reset camera/view button (top-right anchor)
    _VIEW_RESET_OFFSET_RIGHT = 157
    _VIEW_RESET_OFFSET_TOP = 55

    # NPC / char position (CENTER anchor -- char always centered on screen).
    # After reset_camera + NPC selected via surroundings, the NPC is on top
    # of the char (same spot). Offset is from window center.
    _NPC_LOCATION_OFFSET_X = -19
    _NPC_LOCATION_OFFSET_Y = +21

    # ------------------------------------------------------------
    # Offsets ANCHORED TO TEMPLATE (calibrated via cursor 2026-05-24).
    # We find a fixed element (panel title) via matchTemplate and
    # calculate the rest by offset. Works at any window position/size.
    # The title bar delta (capture=window coords, click=client coords) CANCELS
    # out because the offset was measured as (cursor_client - template_center).
    # ------------------------------------------------------------
    _ANCHOR_THRESHOLD = 0.70

    # Surroundings panel (anchors to: Images/misc/surroundings_title.bmp)
    _SURR_TO_SEARCH = (140, 347)        # title -> golden search field
    _SURR_TO_RESULT = (-106, 70)        # title -> 1st result in the list

    # "Dialogue" NPC window (anchors to: npc_dialogue_title.bmp)
    _DIALOGUE_TO_SELL_ITEM = (-114, 181)  # "Dialogue" title -> "Sell Item" button

    # Sell dialog (anchors to: npc_sell_dialog_header.bmp). 6-col x 4-row grid = 24 slots.
    _SELL_TO_SLOT1 = (-97, 43)          # header -> slot 1 (top-left of grid)
    _SELL_COL_SPACING = 34.4
    _SELL_ROW_SPACING = 35.333
    _SELL_TO_CONFIRM = (-76, 461)       # header -> confirm sell button

    # Map (anchors to: map_title.bmp). Game bug: 2 clicks on the same destination don't move,
    # so we do a decoy click in a different region before the real spot.
    _MAP_DUMMY_OFFSET = (60, 0)

    def open_surroundings_ui(self):
        ww, _ = self.get_window_size()
        pos = (ww - self._MINIMAP_SURROUNDINGS_OFFSET_RIGHT,
               self._MINIMAP_SURROUNDINGS_OFFSET_TOP)
        self.logger.info("open_surroundings_ui: window_width=%d, calculated pos=%s", ww, pos)
        self.left_click(pos)
        time.sleep(1.5)

    def map_open(self) -> bool:
        return self._image_finder.is_map_open()

    @contextmanager
    def map(self):
        self.open_map()
        yield
        self.close_map()

    def open_map(self):
        while not self.map_open():
            self.press_key('m')

    def close_map(self):
        while self.map_open():
            self.press_key('m')

    @property
    @abstractmethod
    def inventory_open(self) -> bool: ...

    @contextmanager
    def inventory(self):
        self.open_inventory()
        yield
        self.close_inventory()

    def open_inventory(self):
        while not self.inventory_open:
            self.press_key('i')
            time.sleep(1)

    def close_inventory(self):
        while self.inventory_open:
            self.press_key('i')
            time.sleep(1)

    def _find_anchor(self, bmp_name: str, threshold: float = None) -> tuple[int, int] | None:
        """Center of a template (panel title) in the window; None if not found."""
        return self._image_finder.find_button_center(bmp_name, threshold=threshold or self._ANCHOR_THRESHOLD)

    def search_surroundings(self, val):
        # find the "Surroundings" title; if not found, panel is closed -> open and try again
        title = self._find_anchor('surroundings_title.bmp')
        if title is None:
            self.open_surroundings_ui()
            title = self._find_anchor('surroundings_title.bmp')
        if title is None:
            self.logger.error("search_surroundings: 'Surroundings' title not found (panel visible?)")
            return
        search = (title[0] + self._SURR_TO_SEARCH[0], title[1] + self._SURR_TO_SEARCH[1])
        self.logger.info("search_surroundings: title %s -> search field %s, typing '%s'", title, search, val)
        self.left_click(search)
        time.sleep(0.5)
        for _ in range(15):            # clear previous text (otherwise 'XX' accumulates on re-executions)
            self.press_key('backspace')
        time.sleep(0.3)
        self.type_keys(val)
        time.sleep(1.0)

    def goto_first_surrounding_result(self):
        title = self._find_anchor('surroundings_title.bmp')
        if title is None:
            self.logger.error("goto_first_surrounding_result: 'Surroundings' title not found")
            return
        result = (title[0] + self._SURR_TO_RESULT[0], title[1] + self._SURR_TO_RESULT[1])
        self.logger.info("goto_first_surrounding_result: title %s -> result %s", title, result)
        self.left_click(result)

    def close_surroundings_ui(self):
        # close the panel ONLY if still open (clicking the result may have closed it)
        if self._find_anchor('surroundings_title.bmp') is not None:
            self.open_surroundings_ui()  # minimap eye toggle

    def click_npc(self):
        # NPC is on top of the char, which is always centered on screen.
        ww, wh = self.get_window_size()
        pos = (ww // 2 + self._NPC_LOCATION_OFFSET_X,
               wh // 2 + self._NPC_LOCATION_OFFSET_Y)
        self.logger.info("click_npc: window=%dx%d, calculated pos=%s", ww, wh, pos)
        self.right_click(pos)

    def click_npc_sell_button(self):
        # MAIN: find "Sell Item" text directly by image. Robust to different NPC/menu order
        # (at Blacksmith the 1st line is "Purchase Item", so the fixed offset hits the wrong line).
        # High threshold (0.85) to never hit a near-miss on another line (~0.72).
        sell_item = self._find_anchor('sell_items_button.bmp', threshold=0.85)
        if sell_item is not None:
            # template matches in CAPTURE coords (entire window); convert to client area
            # before clicking (otherwise drops ~1 line below, due to title bar difference)
            click_at = self.window_to_client(sell_item) if hasattr(self, 'window_to_client') else sell_item
            self.logger.info("click_npc_sell_button: 'Sell Item' (template) capture=%s -> client=%s",
                             sell_item, click_at)
            self.left_click(click_at)
            return True
        # FALLBACK: offset from "Dialogue" title (only works if Sell Item is the 1st line).
        dlg = self._find_anchor('npc_dialogue_title.bmp')
        if dlg is None:
            self.logger.error("click_npc_sell_button: neither 'Sell Item' (image) nor 'Dialogue' found "
                              "(NPC window open/visible/on the left?)")
            return False
        sell_item = (dlg[0] + self._DIALOGUE_TO_SELL_ITEM[0], dlg[1] + self._DIALOGUE_TO_SELL_ITEM[1])
        self.logger.warning("click_npc_sell_button: 'Sell Item' image match failed; using offset from "
                            "'Dialogue' %s -> %s (may hit wrong line on some NPCs)", dlg, sell_item)
        self.left_click(sell_item)
        return True

    def reset_camera(self):
        ww, _ = self.get_window_size()
        pos = (ww - self._VIEW_RESET_OFFSET_RIGHT, self._VIEW_RESET_OFFSET_TOP)
        self.logger.info("reset_camera: window_width=%d, calculated pos=%s", ww, pos)
        self.left_click(pos)

    # ------------------------------------------------------------
    # Sell dialog (anchors to: "Sell" header) + 24-slot grid (6 cols x 4 rows)
    # ------------------------------------------------------------
    def sell_dialog_header(self) -> tuple[int, int] | None:
        """Center of the 'Sell' title in the sell dialog. None if not open/visible."""
        return self._find_anchor('npc_sell_dialog_header.bmp')

    def sell_slot_pos(self, header: tuple[int, int], n: int) -> tuple[int, int]:
        """Position of slot n (1-24) of the sell grid, anchored to the header."""
        idx = n - 1
        row, col = idx // 6, idx % 6
        return (int(header[0] + self._SELL_TO_SLOT1[0] + col * self._SELL_COL_SPACING),
                int(header[1] + self._SELL_TO_SLOT1[1] + row * self._SELL_ROW_SPACING))

    def sell_confirm_pos(self, header: tuple[int, int]) -> tuple[int, int]:
        return (header[0] + self._SELL_TO_CONFIRM[0], header[1] + self._SELL_TO_CONFIRM[1])

    def goto_spot_via_map(self, spot_map_offset: tuple[int, int]) -> bool:
        """
        Opens the map (M), clicks the farm spot (decoy click in a different region +
        the real spot, to bypass the game's repeated-click-on-same-destination bug) and
        closes the map. Arrival wait is in the caller (sell.py).
        `spot_map_offset` = offset from 'Map' title (chosen by user in UI).
        """
        self.press_key('m')
        time.sleep(2.0)
        title = self._find_anchor('map_title.bmp')
        if title is None:
            self.press_key('m')   # try opening again
            time.sleep(2.0)
            title = self._find_anchor('map_title.bmp')
        if title is None:
            self.logger.error("goto_spot_via_map: 'Map' not found (map opened?)")
            return False
        spot = (title[0] + spot_map_offset[0], title[1] + spot_map_offset[1])
        dummy = (spot[0] + self._MAP_DUMMY_OFFSET[0], spot[1] + self._MAP_DUMMY_OFFSET[1])
        self.logger.info("goto_spot_via_map: 'Map' %s -> decoy %s -> spot %s", title, dummy, spot)
        self.right_click(dummy)
        time.sleep(0.5)
        self.right_click(spot)
        time.sleep(0.5)
        self.press_key('m')   # close the map to allow movement
        return True

    @abstractmethod
    def team_size(self) -> int: ...

    @property
    @abstractmethod
    def team_members(self) -> list[str]: ...

    @property
    @abstractmethod
    def pet_active(self) -> bool: ...

    @property
    @abstractmethod
    def hp(self) -> int: ...

    @property
    @abstractmethod
    def max_hp(self) -> int: ...

    @property
    @abstractmethod
    def mana(self) -> int: ...

    @property
    @abstractmethod
    def max_mana(self) -> int: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def level(self) -> int: ...

    @property
    @abstractmethod
    def sitting(self) -> bool: ...

    @property
    @abstractmethod
    def in_battle(self) -> str: ...

    @property
    @abstractmethod
    def location(self) -> Location: ...

    @property
    def location_x(self) -> int:
        """
        character location * 20, usually also off by .5
        :returns character location as it appears in game
        """
        return self.location.x

    @property
    def location_y(self) -> int:
        """
        character location * 20, usually also off by .5
        :returns character location as it appears in game
        """
        return self.location.y

    @property
    @abstractmethod
    def location_name(self) -> str | None: ...

    @property
    @abstractmethod
    def target_location(self) -> Location | None: ...

    @property
    @abstractmethod
    def target_id(self) -> str: ...

    @property
    @abstractmethod
    def notification(self) -> bool: ...

    @property
    @abstractmethod
    def has_target(self) -> bool: ...

    @property
    @abstractmethod
    def target_hp(self) -> int | None: ...

    @property
    @abstractmethod
    def target_name(self) -> str | None: ...
