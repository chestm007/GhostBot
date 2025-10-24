from __future__ import  annotations

import time

from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.config import PetConfig
from GhostBot.functions.runner import Runner
from GhostBot.lib.math import seconds

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


class Petfood(Runner):
    
    command_delay = 5

    def __init__(self, client: ExtendedClient):
        super().__init__(client)
        self.config: PetConfig = client.config.pet
        self._last_time_used_petfood = 0
        self._last_time_pet_spawned = 0

    @property
    def _spawn_pet_hotkey(self):
        logger.debug(f"spawn_pet_hotkey: {self.config.bindings.get('spawn')}")
        return self.config.bindings.get('spawn')

    def _run(self) -> None:
        self._feed_pet()
        self._respawn_pet()

    def _feed_pet(self):
        if time.time() - self._last_time_used_petfood > seconds(minutes=int(self.config.food_interval_mins)):
            logger.info(f'{self._client.name}: Feeding pet')
            self._client.press_key(self.config.bindings.get('food'))
            self._last_time_used_petfood = time.time()
            time.sleep(self.command_delay)

    def _despawn_pet(self):
        while self._client.pet_active and self._client.running:
            logger.info(f'{self._client.name}: Despawning pet')
            self._client.press_key(self._spawn_pet_hotkey)
            time.sleep(self.command_delay)

    def _spawn_pet(self):
        while (not self._client.pet_active) and self._client.running:
            logger.info(f'{self._client.name}: Spawning pet')
            self._client.press_key(self._spawn_pet_hotkey)
            time.sleep(self.command_delay)

    def _respawn_pet(self):
        if time.time() - self._last_time_pet_spawned > seconds(minutes=int(self.config.spawn_interval_mins)):
            self._despawn_pet()
            self._spawn_pet()
            self._last_time_pet_spawned = time.time()

