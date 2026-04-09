import asyncio
import time
from abc import ABC, abstractmethod
from collections import namedtuple
from contextlib import asynccontextmanager
from typing import Self, AsyncGenerator, Coroutine

from GhostBot import logger
from GhostBot.lib.talisman_ui_locations import UI_locations

Location = namedtuple('Location', ['x', 'y'])


class AbstractClientWindow(ABC):
    """
    Abstract Class containing all methods expected to interact with the Talisman Online client window.
    """

    @property
    @abstractmethod
    def window_handle(self) -> int: ...

    @abstractmethod
    def set_window_name(self) -> Self: ...

    def new_target(self, _key='tab') -> Self:
        self.press_key(_key)
        return self

    def target_self(self, _key='F1') -> Self:
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

    @asynccontextmanager
    async def mounted(self, _key=None):
        if _key is None:
            yield
            return

        await self.mount(_key)
        yield
        await self.dismount(_key)

    async def mount(self, _key=None):
        if _key is None:
            return

        attempts = 0
        while not self.on_mount and attempts < 3:
            attempts += 1
            self.press_key(_key)
            await asyncio.sleep(4)
        if attempts == 3:
            logger.error("Failed to mount up")

    async def dismount(self, _key=None):
        if _key is None:
            return

        attempts = 0
        while self.on_mount and attempts < 3:
            attempts += 1
            self.press_key(_key)
            await asyncio.sleep(4)
        if attempts == 3:
            logger.error("Failed to dismount")

    @abstractmethod
    def capture_window(self, color: bool): ...

    @abstractmethod
    def press_key(self, key: int | str) -> None: ...

    async def type_keys(self, keys: str) -> None:
        for key in keys.swapcase():
            self.press_key(key)
            await asyncio.sleep(0.1)

    @abstractmethod
    async def left_click(self, pos: tuple[float, float]) -> None: ...

    @abstractmethod
    async def right_click(self, pos: tuple[float, float]) -> None: ...

    @staticmethod
    @abstractmethod
    def get_mouse_window_pos(window_pos: tuple[int, int]) -> Location | None: ...

    @abstractmethod
    def get_window_size_pos(self) -> tuple[Location, Location] | None: ...

    def get_window_pos(self) -> Location:
        return self.get_window_size_pos()[0]

    def get_window_size(self) -> Location:
        return self.get_window_size_pos()[1]

    async def open_surroundings_ui(self):
        await self.left_click(UI_locations.minimap_surroundings)
        await asyncio.sleep(0.5)

    @property
    @abstractmethod
    def inventory_open(self) -> bool: ...

    @asynccontextmanager
    async def inventory(self):
        yield await self.open_inventory()
        await self.close_inventory()

    async def open_inventory(self):
        while not self.inventory_open:
            self.press_key('i')
            await asyncio.sleep(1)

    async def close_inventory(self):
        while self.inventory_open:
            self.press_key('i')
            await  asyncio.sleep(1)

    async def search_surroundings(self, val):
        await self.open_surroundings_ui()
        await self.left_click(UI_locations.surroundings_search)
        await asyncio.sleep(0.5)
        await self.type_keys(val)
        await asyncio.sleep(0.5)

    async def goto_first_surrounding_result(self):
        await self.left_click(UI_locations.surroundings_firstitem)
        await self.open_surroundings_ui()

    async def click_npc(self):
        await self.right_click(UI_locations.npc_location)

    async def reset_camera(self):
        await self.left_click(UI_locations.view_reset)

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
