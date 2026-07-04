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


# Pots in TO are REGEN over ~16s (not instant). Do not re-pot the same key
# before that, or it wastes the pot (right after potting the % still looks low and the bot
# would pot again). Per-key cooldown via Runner._pot_ready/_use_pot.
POT_DURATION_SECS = 16


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
            # optional hook: run NOW (outside interval) if function requests
            # (e.g. Sell._force_run when inventory fills). Opt-in via hasattr.
            if hasattr(self, '_force_run') and self._force_run():
                return True
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
        self._pot_last_used: dict = {}   # pot key -> timestamp of last use

    def _pot_ready(self, key) -> bool:
        """True if pot duration (POT_DURATION_SECS) has passed since last use of THIS
        key -- avoids re-potting while previous pot is still active (duplicate pot)."""
        if not key:
            return False
        return (time.time() - self._pot_last_used.get(key, 0.0)) >= POT_DURATION_SECS

    def _use_pot(self, key) -> bool:
        """Uses pot ONLY if not on cooldown (16s). Returns True if used."""
        if not self._pot_ready(key):
            return False
        self._client.press_key(key)
        self._pot_last_used[key] = time.time()
        return True

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
    ARRIVE_DISTANCE = 10   # when returning to spot, recentralize until ~centered (within this)
    MAP_DISTANCE = 40      # FAR (> this): return via OPEN MAP (reliable); CLOSE: minimap

    def __init__(self, client: BotClientWindow):
        super().__init__(client)
        self.start_location: tuple[int, int] = self.determine_start_location()

    def determine_start_location(self):
        """Returns either the config stored attack_spot, or the current location of the char as the `start_location`"""
        if (attack := self._client.config.attack) is not None:
            if attack.spot is not None:
                return int(attack.spot[0]), int(attack.spot[1])
        if (fairy := self._client.config.fairy) is not None:
            if fairy.spot is not None:
                return int(fairy.spot[0]), int(fairy.spot[1])
        return self._client.location

    def _spot_map_offset(self) -> tuple[int, int] | None:
        """Spot offset on the MAP -- comes from ATTACK config (falls back to sell for compat)."""
        atk = getattr(self._client.config, 'attack', None)
        off = getattr(atk, 'return_spot_map_offset', None) if atk else None
        if not off:
            sell = getattr(self._client.config, 'sell', None)
            off = getattr(sell, 'return_spot_map_offset', None) if sell else None
        return tuple(off) if off else None

    def _goto_start_location(self):
        """Return to spot, HYBRID depending on distance:
          - FAR (> MAP_DISTANCE): open the MAP (M), click-bait + click on spot, close M
            (same as sell -- reliable for far; minimap overflows range and does not move).
          - CLOSE (<= MAP_DISTANCE): small clicks on the MINIMAP (relative to char; the map
            does not move at short distance -- click lands on the char).
        Recentralize until ARRIVE_DISTANCE. Bounded (limited steps + give up) -> does not hang."""
        if not self._client.running:
            return
        if linear_distance(self.start_location, self._client.location) <= self.ARRIVE_DISTANCE:
            return  # already centered enough
        offset = self._spot_map_offset()
        last_dist = None
        for _ in range(8):
            if not self._client.running:
                return
            dist = linear_distance(self.start_location, self._client.location)
            if dist <= self.ARRIVE_DISTANCE:
                return
            if last_dist is not None and dist >= last_dist - 1:  # did not get closer -> give up
                self._log_debug('goto_start: no longer getting closer (dist=%s), continuing', round(dist, 1))
                return
            last_dist = dist
            if dist > self.MAP_DISTANCE:
                # FAR -> OPEN MAP. Needs spot offset on map (captured in UI).
                if offset is None:
                    self._client.set_action("⚠️ Configure 'Farm spot (map)' (📍 Capture spot)")
                    self._log_err("goto_start: char far (%s) but 'Farm spot (map)' not "
                                  "configured -- cannot return via map", round(dist, 1))
                    return
                if self._client.goto_spot_via_map(offset):  # already does click-bait (ghost)
                    t0 = time.time()
                    while (linear_distance(self.start_location, self._client.location) > self.ARRIVE_DISTANCE
                           and self._client.running and time.time() - t0 < 40):
                        time.sleep(1)
            else:
                # CLOSE -> small clicks on minimap
                self._client.move_to_pos_minimap(self.start_location)
