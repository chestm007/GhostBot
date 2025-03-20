from __future__ import annotations
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.lib.math import linear_distance

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


class Runner(ABC):
    """
    base class for any optional function to be ran on the bot, eg fairy, attack, ...
    """
    def __init__(self, client: ExtendedClient):
        self._client = client

    @abstractmethod
    def run(self) -> bool:
        pass


class Locational(Runner):
    start_location = (0, 0)

    def _goto_start_location(self):
        while linear_distance(self.start_location, self._client.location) > 2:
            logger.debug(f'{self._client.name}: go to saved spot: {self.start_location}')
            self._client.move_to_pos(self.start_location)
            time.sleep(0.5)

