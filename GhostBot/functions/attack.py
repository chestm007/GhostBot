from __future__ import annotations

import time

from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.config import AttackConfig
from GhostBot.functions.runner import Locational
from GhostBot.lib.math import linear_distance

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


class AttackContext:
    """
    Object to track changes between now ald last check.

    If it detects a change, it will return true, then set the current values to what it read, and return
    false until they change again
    """
    def __init__(self, client: ExtendedClient, stuck_interval: int) -> None:
        self._client = client
        self._location = self._location = tuple(self._client.location)
        self._target_hp = self._client.target_hp
        self._last_changed_time = time.time()
        self._stuck_interval = stuck_interval
        #self._check_stuck = self._client.config.unstuck

    @property
    def location_changed(self) -> bool:
        loc = tuple(self._location)
        if linear_distance(loc, self._client.location) > 1:
            self._location = self._client.location
            return True
        return False

    @property
    def target_hp_changed(self) -> bool:
        if self._target_hp != self._client.target_hp:
            self._target_hp = self._client.target_hp
            return True
        return False

    @property
    def stuck(self) -> bool:
        # if not self._check_stuck:
        #     return False

        # if target HP or our position changed, we're not stuck
        if self.location_changed or self.target_hp_changed:
            self._last_changed_time = time.time()
            return False

        # if target hp and our position haven't changed in `stuck_interval` we're stuck
        if time.time() - self._last_changed_time > self._stuck_interval:
            self._last_changed_time = time.time()
            return True

        # targethp and location haven't changed, but we aren't past `stuck_interval` we're not stuck
        return False


class Attack(Locational):
    """
    returns True when mob killed or not found

    otherwise returns Falsey
    """
    _cur_attack_queue = []
    def __init__(self, client: ExtendedClient):
        super().__init__(client)
        self.config: AttackConfig = client.config.attack
        try:
            self._stuck_interval = self.config.stuck_interval or 10
            self.roam_distance = self.config.roam_distance or 40
        except AttributeError as e:
            logger.error(f"{self._client.name} error {e}")
            self._stuck_interval = 10

    def _run(self) -> bool:
        self._cur_attack_queue: list[list[int | str]] = list(self.config.attacks)

        context = AttackContext(self._client, self._stuck_interval)
        if self._client.target_hp is None or self._client.target_name == self._client.name or self._client.target_hp < 0:
            logger.debug(f'{self._client.name}: New target')
            self._client.new_target()

        while (self._client.target_hp is not None) and int(self._client.target_hp) >= 0 and self._client.running:
            if self._client.target_name == self._client.name:  # if were targeting ourselves, get a new target
                return True

            # if were too far away from our start location, move back there
            if linear_distance(self.start_location, self._client.location) > 40:
                logger.debug(f'{self._client.name}: too far go back C:{self._client.location} | T:{self.start_location}')
                self._goto_start_location()
                self._client.new_target()
                return True

            # battle pot logic
            self._battle_pots()

            if not self._cur_attack_queue:
                self._cur_attack_queue = list(self.config.attacks)

            key, interval = self._cur_attack_queue.pop(0)
            logger.debug(f'{self._client.name}: ATTACK! {key}  -- {interval}s')
            self._client.press_key(key)
            time.sleep(int(interval) / 1000)

            if context.stuck:  # if we're stuck, get a new target and rerun.
                self._client.new_target()
                return True
        return False

    def _battle_pots(self):
        if self.config.bindings is not None:
            if self.config.bindings.get('battle_hp_pot') is not None and self.config.battle_mana_threshold is not None:
                if self._client.mana_percent < self.config.battle_mana_threshold:
                    self._client.press_key(self.config.bindings.get('battle_mana_pot'))

            if self.config.bindings.get('battle_mana_pot') is not None and self.config.battle_hp_threshold is not None:
                if self._client.hp_percent < self.config.battle_hp_threshold:
                    self._client.press_key(self.config.bindings.get('battle_hp_pot'))
