from __future__ import annotations
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from GhostBot import logger
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

    @abstractmethod
    def run(self) -> bool:
        pass


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
        if hasattr(self._client.config, 'attack_spot'):
            return tuple(self._client.config.attack_spot)
        else:
            return self._client.location

    def _goto_start_location(self):
        """Moves the char to the saved `start_location`"""
        while linear_distance(self.start_location, self._client.location) > 2:
            logger.debug(f'{self._client.name}: go to saved spot: {self.start_location}')
            self._client.move_to_pos(self.start_location)
            time.sleep(2)

