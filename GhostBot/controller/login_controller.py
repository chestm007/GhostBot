from __future__ import annotations

import os
import time
from enum import Enum
from typing import TYPE_CHECKING

import pywintypes

from GhostBot import logger
from GhostBot.image_finder import ImageFinder
from GhostBot.lib.decorators import classproperty
from GhostBot.lib.talisman_ui_locations import UI_locations
from GhostBot.lib.utils import asyncretry, retry

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow
    from collections.abc import Callable


class LoginLock:
    _locked: str = ''
    _waiting: list = list()
    _poll_frequency: float = 1

    def __enter__(self):
        self.acquire(proc_id='context')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    @classmethod
    def acquire(cls, proc_id: str):
        while cls.locked:
            logger.debug('LoginLock :: waiting for lock to be unlocked, polling every %ss', cls._poll_frequency)
            time.sleep(cls._poll_frequency)
        cls._locked = proc_id
        return cls

    @classmethod
    def release(cls):
        cls._locked = ''
        return cls

    @classproperty
    def locked(self):
        return bool(self._locked)

    @classproperty
    def unlocked(self):
        return not bool(self._locked)


class LoginController:
    _login_lock = LoginLock()

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
        success = 4

    @property
    def _enter_credentials(self):
        return bool(self._image_finder.find_ui_element(os.path.join(ImageFinder.misc_folder, 'login_main_page.bmp'),
                                                  threshold=0.6))

    @property
    def _server_select(self):
        return bool(self._image_finder.find_ui_element(os.path.join(ImageFinder.misc_folder, 'login_server_select.bmp')))

    @property
    def _login_queue(self):
        return bool(self._image_finder.find_ui_element(os.path.join(ImageFinder.misc_folder, 'login_queue.bmp')))

    @property
    def _character_select(self):
        if self._client.level:
            return False
        return not any((self._enter_credentials, self._server_select, self._login_queue))

    @property
    def current_stage(self):
        if self._enter_credentials:
            return self.LoginStage.enter_credentials
        elif self._server_select:
            return self.LoginStage.server_select
        elif self._login_queue:
            return self.LoginStage.login_queue
        elif self._character_select:
            return self.LoginStage.character_select
        else:
            return self.LoginStage.success

    def _handle_stage(self):
        match self.current_stage:
            case self.LoginStage.enter_credentials: self._handle_enter_credentials()
            case self.LoginStage.server_select: self._handle_server_select()
            case self.LoginStage.login_queue: self._handle_login_queue()
            case self.LoginStage.character_select: self._handle_character_select()
            case _: raise TypeError(f"unexpected stage {self.current_stage}")

    def _handle_enter_credentials(self):
        logger.debug("LoginController :: %s :: enter credentials", self._client.identifier)
        if self._config:
            char, _conf = self._config
            self._client._name = char
            for _ in range(20):
                self._client.press_key('backspace')
            time.sleep(1)
            self._client.type_keys(_conf.get("username"), char_only=True)
            self._client.press_key("tab")
            self._client.type_keys(_conf.get("password"), char_only=True)
            self._client.press_key("enter")
            if not retry(lambda: self._server_select, 3, 2):
                logger.debug("LoginController :: %s :: login server is busy, restarting login process...", self._client.identifier)
                self._client.left_click((510, 335)) # 'login server is busy' dialog
                time.sleep(0.5)
                self._client.left_click((620, 390))  # username text box

    def _handle_server_select(self):
        self._login_lock.release()
        logger.debug("LoginController :: %s :: server select", self._client.identifier)
        if self._config and (server := self._config[1].get('server')):
            self._client.left_click(UI_locations.server_select.get(server))
            time.sleep(1)
        self._client.left_click(UI_locations.server_select.ok)

    def _handle_login_queue(self):
        logger.debug("LoginController :: %s :: login queue, waiting 30s", self._client.identifier)
        time.sleep(25)

    def _handle_character_select(self):
        logger.debug("LoginController :: %s :: character select", self._client.identifier)
        def select_char(retry_count):
            logger.debug('LoginController :: %s :: waiting for game entered... (attempt %s)', self._client.identifier, retry_count)
            self._client.left_click(UI_locations.char_select_enter_game)
            time.sleep(1)
            self._client.initialize_pointers(force_reload=True)
            return self.current_stage == self.LoginStage.success

        if retry(select_char, 5, 1):
            logger.info("LoginController :: %s :: character logged in", self._client.identifier)
        else:
            logger.info("LoginController :: %s :: character interrupted", self._client.identifier)
            self._client.left_click(UI_locations.char_select_interrupted_ok)

    def handle_login(self, callback: Callable):
        logger.debug("LoginController :: %s :: handle login", self._client.identifier)
        while self._client.level is None:
            try:
                self._client.set_window_name()
                self._handle_stage()
                # Initialize the memory pointers, as they cant be set before login.
                self._client.set_window_name()
            except pywintypes.error as e:
                logger.exception(e)
                if e.args[2] == 'Invalid window handle.':
                    logger.error(f'LoginController :: %s :: ERROR with window handle.', self._client.identifier)
                    break  # jump out of this while loop, skipping the else block.
            except TypeError as e:
                logger.exception(e)
                break
            except Exception as e:
                logger.exception(e)
            time.sleep(1)
        else:
            logger.info("LoginController :: %s :: login handled", self._client.identifier)
            callback(True)
            return
        logger.error("LoginController :: %s :: login failed", self._client.identifier)
        callback(False)


if __name__ == "__main__":
    for i in LoginController.LoginStage:
        print(i.name)