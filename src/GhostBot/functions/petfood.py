"""Pet -- sustain for TWO types of pets, each with its flag (owner's decision):

  - TAMER PET (combat): summons at Start, RE-SUMMONS if dead (detects `pet_active`)
    and feeds every `food_interval_mins`. Only re-summons when DEAD (not by time --
    owner's decision). Spawn key = TOGGLE.
  - NORMAL PET (companion): only FEEDS every `normal_food_interval_mins`
    (presses `normal_food` key). No summon/re-summon.

Each block only acts if the corresponding flag (`tamer_pet` / `normal_pet`) is on.
Combat itself (making pet hit) is NOT here -- it's generic via the Attack tab (combo).
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from GhostBot.functions.runner import Runner
from GhostBot.lib.math import seconds

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow
    from GhostBot.config import PetConfig


class Petfood(Runner):
    _SPAWN_POLL = 10   # 0.5s attempts (=5s) waiting for pet to appear/disappear

    def __init__(self, client: "BotClientWindow"):
        super().__init__(client)
        self.config: PetConfig = client.config.pet
        self._last_feed = 0.0          # Tamer pet food
        self._last_normal_feed = 0.0   # normal pet food

    def _run(self) -> bool:
        if self.config.tamer_pet:
            self._run_tamer_pet()
        if self.config.normal_pet:
            self._feed_normal_pet()
        return True

    # ---------------------------------------------------------- TAMER PET
    def _run_tamer_pet(self) -> None:
        b = self.config.bindings or {}
        spawn = b.get('spawn')
        food = b.get('food')

        # Pet dead/absent -> RE-SUMMON (sustain). Also covers initial summon.
        if spawn and not self._client.pet_active:
            self._client.set_action("🐾 Summoning pet")
            self._log_info("Tamer pet absent -> summoning")
            self._spawn_pet(spawn)
            return   # summoned -> rest left for next cycle (but normal pet still runs)

        # Periodic food for Tamer pet
        if food and self.config.food_interval_mins:
            if time.time() - self._last_feed >= seconds(minutes=int(self.config.food_interval_mins)):
                self._client.set_action("🐾 Feeding pet (Tamer)")
                self._log_info("feeding Tamer pet")
                self._client.press_key(food)
                self._last_feed = time.time()

    # ---------------------------------------------------------- NORMAL PET
    def _feed_normal_pet(self) -> None:
        food = (self.config.bindings or {}).get('normal_food')
        if not food or not self.config.normal_food_interval_mins:
            return
        if time.time() - self._last_normal_feed >= seconds(minutes=int(self.config.normal_food_interval_mins)):
            self._client.set_action("🐾 Feeding pet (normal)")
            self._log_info("feeding normal pet")
            self._client.press_key(food)
            self._last_normal_feed = time.time()

    # ---------------------------------------------------------- helpers
    def _spawn_pet(self, spawn) -> None:
        """Presses spawn key and waits for pet to appear. Bounded (does not hang); if it
        does not appear, next cycle tries again."""
        self._client.press_key(spawn)
        for _ in range(self._SPAWN_POLL):
            if not self._client.running or self._client.pet_active:
                return
            time.sleep(0.5)
