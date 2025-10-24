from __future__ import annotations

import time
from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.config import RegenConfig
from GhostBot.functions.runner import Locational

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


class Regen(Locational):
    def __init__(self, client: ExtendedClient):
        super().__init__(client=client)

        self.config: RegenConfig = self._client.config.regen
        self._mana_threshold = float(self.config.mana_threshold or 0.75)
        self._hp_threshold = float(self.config.hp_threshold or 0.75)

    def _run(self) -> bool:
        """
        :return: True is we healed successfully, False if we were attacked, or in battle while healing
        """
        if self._mana_low() or self._hp_low():
            self._goto_start_location()

            if not self._client.in_battle:
                logger.info(f'{self._client.name}: low hp/mana, starting Regen')

                # mana/hp pots\
                if self.config.bindings.get('hp_pot') is not None:
                    if self._client.hp_percent < self._hp_threshold:
                        self._use_hp_pot()
                if self.config.bindings.get('mana_pot') is not None:
                    if self._client.mana_percent < self._mana_threshold:
                        self._use_mana_pot()

                hp = int(self._client.hp)
                while (self._client.hp < self._client.max_hp or self._client.mana < self._client.max_mana) and self._client.running:
                    logger.debug(f'{self._client.name}: healing')
                    time.sleep(2)
                    if self._client.in_battle or self._client.hp < hp:
                        logger.debug(f'{self._client.name}: Ouch, attacking')
                        return False
                    self._goto_spot_and_sit()
                    hp = int(self._client.hp)
                return True
        return False

    def _mana_low(self) -> int:
        return self._client.mana_percent < self._mana_threshold

    def _hp_low(self) -> int:
        return self._client.hp_percent < self._hp_threshold

    def _use_hp_pot(self) -> None:
        self._goto_spot_and_sit()
        self._client.press_key(self.config.bindings.get('hp_pot'))

    def _use_mana_pot(self) -> None:
        self._goto_spot_and_sit()
        self._client.press_key(self.config.bindings.get('mana_pot'))

    def _goto_spot_and_sit(self) -> None:
        self._goto_start_location()
        self._sit()

    def _sit(self):
        if not self._client.sitting:
            logger.debug(f'{self._client.name}: sitting')
            self._client.press_key(self.config.bindings.get('sit'))
