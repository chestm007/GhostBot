from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Any

from GhostBot import logger as _logger
from GhostBot.enums.bot_status import BotStatus
from GhostBot.lib.math import linear_distance

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow


def run_at_interval(run_on_start: bool = False, run_in_battle: bool = False):
    def inner(_clazz):
        _init = _clazz.__init__
        def init(self, *args, **kwargs):
            self._last_time_ran = 0 if run_on_start else time.time()
            ret = _init(self, *args, **kwargs)

            if hasattr(_clazz, '_setup'):
                self._log_debug("%s :: %s :: running function setup", self.__class__.__name__, self._client.name)
                _clazz._setup(self)

            if not hasattr(self, '_interval'):
                raise AttributeError(f"Abstract property _interval not defined for {self.__class__.__name__}")
            return ret

        _run = _clazz.run
        def run(self: Runner, *args, **kwargs):
            if should_run(self):
                self._log_debug("%s :: %s :: running function", self.__class__.__name__, self._client.name)
                self._last_time_ran = time.time()
                _run(self, *args, **kwargs)

        def should_run(self):
            if not run_in_battle and self._client.in_battle:
                return False
            return time.time() - self._last_time_ran > self._interval

        _clazz.__init__ = init
        _clazz.run = run
        return _clazz
    return inner

# TODO: class that interacts with NPC's, probably extend Locational

class InjectedLoggingMixin(ABC):

    def __init__(self, client: BotClientWindow):
        self.logger = _logger.getChild(self.__class__.__name__)
        self._error_loggers = [self.logger.error]
        self._info_loggers = [self.logger.info]
        self._debug_loggers = [self.logger.debug]
        self._client = client
        if not self.__class__.__name__.endswith('Context'):
            self._log_debug(f"initializing {self.__class__.__name__}...")

    def add_logger(self, _logger: Callable[[str], Any], level: int = logging.INFO):
        if level < logging.INFO:
            self._debug_loggers.append(_logger)
        if level < logging.ERROR:
            self._info_loggers.append(_logger)
        self._error_loggers.append(_logger)

    def _log_err(self, msg: str, *args) -> None:
        all(map(lambda f: f(f"{self._client.name}: {msg}", *args), self._error_loggers))

    def _log_info(self, msg: str, *args) -> None:
        all(map(lambda f: f(f"{self._client.name}: {msg}", *args), self._info_loggers))

    def _log_debug(self, msg: str, *args) -> None:
        all(map(lambda f: f(f"{self._client.name}: {msg}", *args), self._debug_loggers))

class Runner(InjectedLoggingMixin, ABC):
    """
    base class for any optional function to be run on the bot, eg. fairy, attack, ...
    """
    def __init__(self, client: BotClientWindow):
        super().__init__(client)

    def run(self):
        if self._client.bot_status == BotStatus.running:
            return self._run()
        self._log_debug("not running as client not in running status.")
        return None

    @abstractmethod
    def _run(self) -> bool: ...


class Locational(Runner, ABC):
    """
    Represents a function that has a concept of location.
    """

    def __init__(self, client: BotClientWindow):
        super().__init__(client)
        self.start_location: tuple[int, int] = self.determine_start_location()

    def determine_start_location(self):
        """Returns either the config stored attack_spot, or the current location of the char as the `start_location`"""
        if (attack := self._client.config.attack) is not None:
            if attack.spot is not None:
                return int(attack.spot[0]), int(attack.spot[1])
        return self._client.location

    def _goto_start_location(self):
        """Moves the char to the saved `start_location`"""
        while linear_distance(self.start_location, self._client.location) > 2 and self._client.running:
            self._log_debug(f'{self._client.name}: go to saved spot: {self.start_location}')
            self._client.move_to_pos(self.start_location)
