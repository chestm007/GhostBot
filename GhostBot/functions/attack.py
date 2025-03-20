import time

from GhostBot import logger
from GhostBot.functions.runner import Locational
from GhostBot.lib import vk_codes
from GhostBot.lib.math import linear_distance


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
        if self._client.target_hp is None or self._client.target_name == self._client.name or self._client.target_hp < 0:
            logger.debug(f'{self._client.name}: New target')
            self._client.new_target()
            # TODO: return True

        last_time = time.time()
        while self._client.target_hp and int(self._client.target_hp) >= 0 and self._client.running:
            if self._client.target_name == self._client.name:  # if were targeting ourself, get a new target
                # TODO: return True
                break

            # if were too far away from our start location, move back there
            if linear_distance(self.start_location, self._client.location) > 30:
                logger.info(f'{self._client.name}: too far go back C:{self._client.location} | T:{self.start_location}')
                self._goto_start_location()
                # TODO: return True
                break  # get a new target near our start position

            # battle pot logic
            if self._client.config.bindings.get('battle_hp_pot') is not None:
                if self._client.mana_percent < self._client.config.battle_mana_threshold:
                    self._client.press_key(vk_codes[self._client.config.bindings.get('battle_mana_pot')])

            if self._client.config.bindings.get('battle_mana_pot') is not None:
                if self._client.hp_percent < self._client.config.battle_hp_threshold:
                    self._client.press_key(vk_codes[self._client.config.bindings.get('battle_hp_pot')])

            if not self._cur_attack_queue:
                self._cur_attack_queue = list(self._client.config.attacks)
            logger.debug(f'{self._client.name}: ATTACK!')
            key, interval = self._cur_attack_queue.pop()
            self._client.press_key(vk_codes[key])
            time.sleep(interval)

            if time.time() - last_time > 10:  # if we havent moved after we tried attacking, we stuck.
                self._client.new_target()
                # TODO: return True
                break
