from __future__ import annotations

import asyncio
import os
from enum import Enum
from typing import TYPE_CHECKING

import pywintypes

from GhostBot import logger
from GhostBot.image_finder import ImageFinder
from GhostBot.lib.talisman_ui_locations import UI_locations

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow
    from collections.abc import Callable


class LoginController:
    def __init__(self, client: "BotClientWindow"):
        self._client = client
        self._config: tuple[str, dict[str, str]] | None = None
        self._image_finder = ImageFinder(client)

    def set_config(self, config: tuple[str, dict[str, str]]):
        self._config = config

    class LoginStage(Enum):
        enter_credentials = 0
        server_select = 1
        login_queue = 2
        character_select = 3

    @property
    def _enter_credentials(self):
        return self._image_finder.find_ui_element(os.path.join(ImageFinder.misc_folder, 'login_main_page.bmp'),
                                                  threshold=0.6)

    @property
    def _server_select(self):
        return self._image_finder.find_ui_element(os.path.join(ImageFinder.misc_folder, 'login_server_select.bmp'))

    @property
    def _login_queue(self):
        return self._image_finder.find_ui_element(os.path.join(ImageFinder.misc_folder, 'login_queue.bmp'))

    @property
    def _character_select(self):
        return not any((self._enter_credentials, self._server_select, self._login_queue))

    @property
    def current_stage(self):
        if self._enter_credentials:
            return self.LoginStage.enter_credentials
        elif self._server_select:
            return self.LoginStage.server_select
        elif self._login_queue:
            return self.LoginStage.login_queue
        else:
            return self.LoginStage.character_select

    async def _handle_stage(self):
        match self.current_stage:
            case self.LoginStage.enter_credentials: await self._handle_enter_credentials()
            case self.LoginStage.server_select: await self._handle_server_select()
            case self.LoginStage.login_queue: await self._handle_login_queue()
            case self.LoginStage.character_select: await self._handle_character_select()
            case _: raise TypeError(f"unexpected stage {self.current_stage}")

    async def _handle_enter_credentials(self):
        logger.debug(f"{self.__class__.__name__} :: {self._client.process_id} :: enter credentials")
        if self._config:
            char, _conf = self._config
            self._client._name = char
            for _ in range(20):
                self._client.press_key('backspace')
            await asyncio.sleep(1)
            await self._client.type_keys(_conf.get("username"))
            self._client.press_key("tab")
            await self._client.type_keys(_conf.get("password"))
            self._client.press_key("enter")
            await asyncio.sleep(4)

    async def _handle_server_select(self):
        logger.debug(f"{self.__class__.__name__} :: {self._client.process_id} :: server select")
        if self._config and (server := self._config[1].get('server')):
            await self._client.left_click(UI_locations.server_select.get(server))
            await asyncio.sleep(1)
        await self._client.left_click(UI_locations.server_select.ok)

    async def _handle_login_queue(self):
        logger.debug(f"{self.__class__.__name__} :: {self._client.process_id} :: login queue, waiting 30s")
        await asyncio.sleep(25)

    async def _handle_character_select(self):
        logger.debug(f"{self.__class__.__name__} :: {self._client.process_id} :: character select")
        retries = 0
        while retries <= 3:
            await self._client.left_click(UI_locations.char_select_enter_game)
            await asyncio.sleep(1)
            if not self._character_select:
                logger.debug(f"{self.__class__.__name__} :: {self._client.process_id} :: character logged in")
                break
            retries += 1
        else:
            logger.debug(f"{self.__class__.__name__} :: {self._client.process_id} :: character interrupted")
            await self._client.left_click(UI_locations.char_select_interrupted_ok)

    async def handle_login(self, callback: Callable):
        logger.debug(f"{self.__class__.__name__} :: {self._client.process_id} :: handle login")
        while self._client.level is None:
            try:
                self._client.set_window_name()
                await self._handle_stage()
                self._client.set_window_name()
            except pywintypes.error as e:
                logger.exception(e)
                if e.args[2] == 'Invalid window handle.':
                    logger.error(f'{self.__class__.__name__} :: {self._client.process_id} :: ERROR with window handle.')
                    break  # jump out of this while loop, skipping the else block.
            await asyncio.sleep(5)
        else:
            logger.debug(f"{self.__class__.__name__} :: {self._client.process_id} :: login handled")
            await callback(True)
            return
        logger.debug(f"{self.__class__.__name__} :: {self._client.process_id} :: login failed")
        await callback(False)


if __name__ == "__main__":
    for i in LoginController.LoginStage:
        print(i.name)