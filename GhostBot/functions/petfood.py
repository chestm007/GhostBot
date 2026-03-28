from __future__ import  annotations

import asyncio
import time

from typing import TYPE_CHECKING

from GhostBot.config import PetConfig
from GhostBot.functions.runner import Runner, run_at_interval
from GhostBot.lib.math import seconds

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow


@run_at_interval()
class Petfood(Runner):
    
    command_delay = 5

    def __init__(self, client: BotClientWindow):
        super().__init__(client)
        self.config: PetConfig = client.config.pet
        self._interval = seconds(minutes=int(self.config.food_interval_mins))
        self._last_time_pet_spawned = 0

    async def _setup(self):
        await self._spawn_pet()

    @property
    def _spawn_pet_hotkey(self):
        self._log_debug(f"spawn_pet_hotkey: {self.config.bindings.get('spawn')}")
        return self.config.bindings.get('spawn')

    async def _run(self) -> None:
        await self._feed_pet()
        await self._respawn_pet()

    async def _feed_pet(self):
        self._log_info(f'Feeding pet')
        self._client.press_key(self.config.bindings.get('food'))
        await asyncio.sleep(self.command_delay)

    async def _despawn_pet(self):
        while self._client.pet_active and self._client.running:
            self._log_info(f'Despawning pet')
            self._client.press_key(self._spawn_pet_hotkey)
            poll = 0
            while self._client.pet_active and self._client.running and poll < 10:
                poll += 1
                await asyncio.sleep(0.5)

    async def _spawn_pet(self):
        while (not self._client.pet_active) and self._client.running:
            self._log_info(f'Spawning pet')
            self._client.press_key(self._spawn_pet_hotkey)
            poll = 0
            while (not self._client.pet_active) and self._client.running and poll < 10:
                poll += 1
                await asyncio.sleep(0.5)

    async def _respawn_pet(self):
        if time.time() - self._last_time_pet_spawned > seconds(minutes=int(self.config.spawn_interval_mins)):
            await self._despawn_pet()
            await self._spawn_pet()
            self._last_time_pet_spawned = time.time()

