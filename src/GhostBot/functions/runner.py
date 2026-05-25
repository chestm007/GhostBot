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
    ACCEPT_DISTANCE = 100   # dentro disso = ja na area do spot -> nao precisa voltar, so ataca
    ARRIVE_DISTANCE = 50    # ao voltar pelo mapa, considera "chegou" dentro disso

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
        """Offset do spot no MAPA (capturado na aba Sell -- mesmo ponto de farm)."""
        sell = getattr(self._client.config, 'sell', None)
        off = getattr(sell, 'return_spot_map_offset', None) if sell else None
        return tuple(off) if off else None

    def _goto_start_location(self):
        """Volta pro spot pelo MAPA ABERTO (igual o sell: abre M, clique-ISCA pra furar
        o bug do jogo, clica no spot, fecha M). So volta se estiver LONGE
        (> ACCEPT_DISTANCE); dentro disso ja esta na area do spot e segue atacando.
        O mapa nao serve pra dist curta (o clique cai quase em cima do char), por isso
        so usamos pra longe. Bounded (poucas viagens + desiste) -> nunca trava/foge."""
        if not self._client.running:
            return
        if linear_distance(self.start_location, self._client.location) <= self.ACCEPT_DISTANCE:
            return  # ja esta na area do spot
        offset = self._spot_map_offset()
        if offset is None:
            self._log_err("goto_start: 'Spot de farm (mapa)' nao configurado -- nao da pra voltar")
            return
        last_dist = None
        for _ in range(3):
            if not self._client.running:
                return
            dist = linear_distance(self.start_location, self._client.location)
            if dist <= self.ARRIVE_DISTANCE:
                return
            if last_dist is not None and dist >= last_dist - 3:  # nao aproximou -> desiste
                self._log_debug('goto_start: mapa nao aproximou (dist=%s), seguindo', round(dist, 1))
                return
            last_dist = dist
            if not self._client.goto_spot_via_map(offset):  # ja inclui o clique-isca (fantasma)
                return
            t0 = time.time()
            while linear_distance(self.start_location, self._client.location) > self.ARRIVE_DISTANCE and self._client.running:
                if time.time() - t0 > 40:
                    self._log_debug('goto_start: timeout no retorno por mapa')
                    break
                time.sleep(1)
