"""Pet (Tamer) -- sustentacao do pet: invoca, alimenta e RE-INVOCA se morrer.

Reconstruido 2026-05-27 (antes era um stub). O combate em si (mandar o pet bater) NAO
fica aqui -- e' generico pela aba Attack (o Tamer poe a tecla do pet no combo). Esta
funcao so MANTEM o pet vivo e alimentado:

- invoca no Start (se nao houver pet) e RE-INVOCA sempre que o pet morre/some
  (detectado por `client.pet_active` -- checado a cada ciclo, resposta rapida);
- alimenta a cada `food_interval_mins` (aperta a tecla de comida);
- re-invocacao periodica OPCIONAL (`spawn_interval_mins`): despawn + spawn pra renovar
  um pet que expira sozinho. Em branco = so re-invoca quando morre.

A tecla de spawn e' um TOGGLE (aperta com pet ativo = despawn; sem pet = invoca).
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
        self._last_feed = 0.0
        self._last_refresh = time.time()   # nao renova logo no Start (acabou de invocar)

    def _run(self) -> bool:
        b = self.config.bindings or {}
        spawn = b.get('spawn')
        food = b.get('food')

        # 1) Pet morto/ausente -> RE-INVOCA (sustain). Cobre tambem o summon inicial.
        if spawn and not self._client.pet_active:
            self._client.set_action("🐾 Invocando o pet")
            self._log_info("pet ausente -> invocando")
            self._spawn_pet(spawn)
            return True

        # 2) Comida periodica
        if food and self.config.food_interval_mins:
            if time.time() - self._last_feed >= seconds(minutes=int(self.config.food_interval_mins)):
                self._client.set_action("🐾 Alimentando o pet")
                self._log_info("alimentando o pet")
                self._client.press_key(food)
                self._last_feed = time.time()

        # 3) Re-invocacao periodica OPCIONAL (pet que expira) -- em branco = nao faz
        if spawn and self.config.spawn_interval_mins:
            if time.time() - self._last_refresh >= seconds(minutes=int(self.config.spawn_interval_mins)):
                self._refresh_pet(spawn)
                self._last_refresh = time.time()
        return True

    def _spawn_pet(self, spawn) -> None:
        """Aperta a tecla de spawn e espera o pet aparecer. Bounded (nao trava); se nao
        aparecer, o proximo ciclo tenta de novo."""
        self._client.press_key(spawn)
        for _ in range(self._SPAWN_POLL):
            if not self._client.running or self._client.pet_active:
                return
            time.sleep(0.5)

    def _refresh_pet(self, spawn) -> None:
        """Renova o pet: despawn (toggle) -> espera sumir -> invoca de novo."""
        self._client.set_action("🐾 Renovando o pet")
        self._log_info("renovando o pet (despawn + spawn)")
        if self._client.pet_active:
            self._client.press_key(spawn)
            for _ in range(self._SPAWN_POLL):
                if not self._client.running or not self._client.pet_active:
                    break
                time.sleep(0.5)
        self._spawn_pet(spawn)
