import time

from GhostBot import logger
from GhostBot.functions.runner import Locational


class Regen(Locational):
    def run(self) -> bool:
        """
        :return: True is we healed successfully, False if we were attacked, or in battle while healing
        """
        if self._mana_low() or self._hp_low():
            self._goto_start_location()

            if not self._client.in_battle:
                logger.info(f'{self._client.name}: low hp/mana, starting Regen')

                # mana/hp pots\
                if self._client.config.bindings.get('hp_pot') is not None:
                    if self._client.hp_percent < self._client.config.hp_threshold:
                        self._use_hp_pot()
                if self._client.config.bindings.get('mana_pot') is not None:
                    if self._client.mana_percent < self._client.config.mana_threshold:
                        self._use_mana_pot()

                hp = int(self._client.hp)
                while self._client.hp < self._client.max_hp or self._client.mana < self._client.max_mana:
                    logger.debug(f'{self._client.name}: healing')
                    time.sleep(0.5)
                    if self._client.in_battle or self._client.hp < hp:
                        logger.debug(f'{self._client.name}: Ouch, attacking')
                        return False
                    hp = int(self._client.hp)
                return True
        return False

    def _mana_low(self) -> int:
        return self._client.mana_percent < self._client.config.mana_threshold

    def _hp_low(self) -> int:
        return self._client.hp_percent < self._client.config.hp_threshold

    def _use_hp_pot(self) -> None:
        self._goto_spot_and_sit()
        self._client.press_key(self._client.config.bindings.get('hp_pot'))

    def _use_mana_pot(self) -> None:
        self._goto_spot_and_sit()
        self._client.press_key(self._client.config.bindings.get('mana_pot'))

    def _goto_spot_and_sit(self) -> None:
        self._goto_start_location()
        if not self._client.sitting:
            logger.debug(f'{self._client.name}: sitting')
            self._client.press_key(self._client.config.bindings.get('sit'))
