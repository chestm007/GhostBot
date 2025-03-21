from __future__ import annotations

import time

from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.functions.runner import Locational
from GhostBot.lib import vk_codes
from GhostBot.lib.math import linear_distance

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


class AttackContext:
    """
    Object to track changes between now ald last check.

    If it detects a change, it will return true, then set the current values to what it read, and return
    false until they change again
    """
    def __init__(self, client: ExtendedClient):
        self._client = client
        self._location = self._location = tuple(self._client.location)
        self._target_hp = self._client.target_hp
        self._last_changed_time = time.time()
        #self._check_stuck = self._client.config.unstuck

    @property
    def location_changed(self):
        loc = tuple(self._location)
        if linear_distance(loc, self._client.location) > 1:
            self._location = self._client.location
            return True
        return False

    @property
    def target_hp_changed(self):
        if self._target_hp != self._client.target_hp:
            self._target_hp = self._client.target_hp
            return True
        return False

    @property
    def stuck(self):
        # if not self._check_stuck:
        #     return False

        # if target HP or our position changed, we're not stuck
        if self.location_changed or self.target_hp_changed:
            self._last_changed_time = time.time()
            return False

        # if target hp and our position haven't changed in `stuck_interval` we're stuck
        if time.time() - self._last_changed_time > self._client.config.stuck_interval:
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

    def run(self) -> bool:
        self._cur_attack_queue: list[str] = list(self._client.config.attacks)
        return self._run()

    def _run(self) -> bool:
        context = AttackContext(self._client)
        if self._client.target_hp is None or self._client.target_name == self._client.name or self._client.target_hp < 0:
            logger.debug(f'{self._client.name}: New target')
            self._client.new_target()

        while self._client.target_hp and int(self._client.target_hp) >= 0 and self._client.running:
            if self._client.target_name == self._client.name:  # if were targeting ourselves, get a new target
                return True

            # if were too far away from our start location, move back there
            if linear_distance(self.start_location, self._client.location) > 40:
                logger.debug(f'{self._client.name}: too far go back C:{self._client.location} | T:{self.start_location}')
                self._goto_start_location()
                self._client.new_target()
                return True

            # battle pot logic
            if self._client.config.bindings.get('battle_hp_pot') is not None:
                if self._client.mana_percent < self._client.config.battle_mana_threshold:
                    self._client.press_key(vk_codes[self._client.config.bindings.get('battle_mana_pot')])

            if self._client.config.bindings.get('battle_mana_pot') is not None:
                if self._client.hp_percent < self._client.config.battle_hp_threshold:
                    self._client.press_key(vk_codes[self._client.config.bindings.get('battle_hp_pot')])

            if not self._cur_attack_queue:
                self._cur_attack_queue = list(self._client.config.attacks)

            key, interval = self._cur_attack_queue.pop()
            logger.debug(f'{self._client.name}: ATTACK! {key}  -- {interval}s')
            self._client.press_key(vk_codes[key])
            time.sleep(interval)

            if context.stuck:  # if we're stuck, get a new target and rerun.
                self._client.new_target()
                return True
