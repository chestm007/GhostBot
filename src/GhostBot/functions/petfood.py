"""Pet -- sustentacao de DOIS tipos de pet, cada um com sua flag (decisao do dono):

  - PET DO TAMER (combate): invoca no Start, RE-INVOCA se morrer (detecta `pet_active`),
    alimenta a cada `food_interval_mins`, re-invocacao periodica OPCIONAL
    (`spawn_interval_mins`; vazio = so quando morre). Tecla de spawn = TOGGLE.
  - PET NORMAL (companheiro): so ALIMENTA a cada `normal_food_interval_mins`
    (aperta a tecla `normal_food`). Sem invocar/re-invocar.

Cada bloco so age se a flag correspondente (`tamer_pet` / `normal_pet`) estiver ligada.
O combate em si (mandar o pet bater) NAO fica aqui -- e' generico pela aba Attack (combo).
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
    _SPAWN_POLL = 10   # tentativas de 0.5s (=5s) esperando o pet aparecer/sumir

    def __init__(self, client: "BotClientWindow"):
        super().__init__(client)
        self.config: PetConfig = client.config.pet
        self._last_feed = 0.0          # comida do pet do Tamer
        self._last_normal_feed = 0.0   # comida do pet normal
        self._last_refresh = time.time()   # nao renova logo no Start (acabou de invocar)

    def _run(self) -> bool:
        if self.config.tamer_pet:
            self._run_tamer_pet()
        if self.config.normal_pet:
            self._feed_normal_pet()
        return True

    # ---------------------------------------------------------- PET DO TAMER
    def _run_tamer_pet(self) -> None:
        b = self.config.bindings or {}
        spawn = b.get('spawn')
        food = b.get('food')

        # Pet morto/ausente -> RE-INVOCA (sustain). Cobre tambem o summon inicial.
        if spawn and not self._client.pet_active:
            self._client.set_action("🐾 Invocando o pet")
            self._log_info("pet do Tamer ausente -> invocando")
            self._spawn_pet(spawn)
            return   # invocou -> o resto fica pro proximo ciclo (mas o pet normal ainda roda)

        # Comida periodica do pet do Tamer
        if food and self.config.food_interval_mins:
            if time.time() - self._last_feed >= seconds(minutes=int(self.config.food_interval_mins)):
                self._client.set_action("🐾 Alimentando o pet (Tamer)")
                self._log_info("alimentando o pet do Tamer")
                self._client.press_key(food)
                self._last_feed = time.time()

        # Re-invocacao periodica OPCIONAL (pet que expira) -- vazio = nao faz
        if spawn and self.config.spawn_interval_mins:
            if time.time() - self._last_refresh >= seconds(minutes=int(self.config.spawn_interval_mins)):
                self._refresh_pet(spawn)
                self._last_refresh = time.time()

    # ---------------------------------------------------------- PET NORMAL
    def _feed_normal_pet(self) -> None:
        food = (self.config.bindings or {}).get('normal_food')
        if not food or not self.config.normal_food_interval_mins:
            return
        if time.time() - self._last_normal_feed >= seconds(minutes=int(self.config.normal_food_interval_mins)):
            self._client.set_action("🐾 Alimentando o pet (normal)")
            self._log_info("alimentando o pet normal")
            self._client.press_key(food)
            self._last_normal_feed = time.time()

    # ---------------------------------------------------------- helpers
    def _spawn_pet(self, spawn) -> None:
        """Aperta a tecla de spawn e espera o pet aparecer. Bounded (nao trava); se nao
        aparecer, o proximo ciclo tenta de novo."""
        self._client.press_key(spawn)
        for _ in range(self._SPAWN_POLL):
            if not self._client.running or self._client.pet_active:
                return
            time.sleep(0.5)

    def _refresh_pet(self, spawn) -> None:
        """Renova o pet do Tamer: despawn (toggle) -> espera sumir -> invoca de novo."""
        self._client.set_action("🐾 Renovando o pet")
        self._log_info("renovando o pet do Tamer (despawn + spawn)")
        if self._client.pet_active:
            self._client.press_key(spawn)
            for _ in range(self._SPAWN_POLL):
                if not self._client.running or not self._client.pet_active:
                    break
                time.sleep(0.5)
        self._spawn_pet(spawn)
