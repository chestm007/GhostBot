from __future__ import annotations
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.enums.bot_status import BotStatus
from GhostBot.lib.math import linear_distance

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


# TODO: class that interacts with NPC's, probably extend Locational


class Runner(ABC):
    """
    base class for any optional function to be run on the bot, eg. fairy, attack, ...
    """
    def __init__(self, client: ExtendedClient):
        self._client = client
        self._log_debug(f"initializing {self.__class__.__name__}...")

    def run(self):
        if self._client.bot_status == BotStatus.running:
            return self._run()
        self._log_debug("not running as client not in running status.")
        return None

    @abstractmethod
    def _run(self) -> bool:
        pass

    def _log_err(self, msg: str) -> None:
        logger.error(f"{self._client.name}: {msg}")

    def _log_info(self, msg: str) -> None:
        logger.info(f"{self._client.name}: {msg}")

    def _log_debug(self, msg: str) -> None:
        logger.debug(f"{self._client.name}: {msg}")


class Locational(Runner, ABC):
    """
    Represents a function that has a concept of location.
    """

    def __init__(self, client: ExtendedClient):
        super().__init__(client)
        self.start_location: tuple[int, int] = self.determine_start_location()

    # TODO: implement map navigation when X distance away

    def determine_start_location(self):
        """Returns either the config stored attack_spot, or the current location of the char as the `start_location`"""
        if (regen := self._client.config.regen) is not None:
            if regen.spot is not None:
                return regen.spot
        return self._client.location

    def _goto_start_location(self):
        """Moves the char to the saved `start_location`"""
        while linear_distance(self.start_location, self._client.location) > 2 and self._client.running:
            logger.debug(f'{self._client.name}: go to saved spot: {self.start_location}')
            self._client.move_to_pos(self.start_location)
            time.sleep(2)

    def _block_while_moving(self):
        while self._client.running:
            _location = self._client.location
            time.sleep(3)
            if linear_distance(self._client.location, _location) < 1:
                break
