from __future__ import  annotations

import time

from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.functions.runner import Runner
from GhostBot.lib.math import seconds

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


class Petfood(Runner):
    
    command_delay = 5

    def __init__(self, client: ExtendedClient):
        super().__init__(client)
        self._last_time_used_petfood = 0
        self._last_time_pet_spawned = 0

    @property
    def _spawn_pet_hotkey(self):
        logger.debug(f"spawn_pet_hotkey: {self._client.config.bindings.get('pet')}")
        return self._client.config.bindings.get('pet')

    def run(self) -> bool:
        self._feed_pet()

    def _feed_pet(self):
        if time.time() - self._last_time_used_petfood > seconds(minutes=self._client.config.petfood_interval):
            logger.info(f'{self._client.name}: Feeding pet')
            self._client.press_key(self._client.config.bindings.get('petfood'))
            self._last_time_used_petfood = time.time()
            time.sleep(self.command_delay)

    def _respawn_pet(self):
        # TODO: we need a way to check if the pet is summoned, at the moment this is flakey.

        if time.time() - self._last_time_pet_spawned > seconds(hours=4):
            while self._client.pet_active:
                print('despawn')
                self._client.press_key(self._spawn_pet_hotkey)
                time.sleep(self.command_delay)

            while not self._client.pet_active:
                print('spawn')
                self._client.press_key(self._spawn_pet_hotkey)
                time.sleep(self.command_delay)
            self._last_time_pet_spawned = time.time()

