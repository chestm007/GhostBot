import time

from GhostBot import logger
from GhostBot.functions.runner import Runner
from GhostBot.lib import vk_codes


class Petfood(Runner):

    _last_time_used_petfood = 0

    def run(self) -> bool:
        if time.time() - self._last_time_used_petfood > 60 * self._client.config.petfood_interval:
            logger.info(f'{self._client.name}: Feeding pet')
            self._client.press_key(vk_codes[self._client.config.bindings.get('petfood')])
            self._last_time_used_petfood = time.time()
            time.sleep(2)
