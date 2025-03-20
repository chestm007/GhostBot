import time

from GhostBot import logger
from GhostBot.functions.runner import Runner
from GhostBot.lib import vk_codes


class Buffs(Runner):

    _last_time_used_buffs = 0

    def run(self) -> None:
        if time.time() - self._last_time_used_buffs > 60 * self._client.config.buff_interval:
            logger.info(f'{self._client.name}: Buffing.')
            for buff in self._client.config.bindings.get('buffs'):
                self._client.press_key(vk_codes[buff])
                self._last_time_used_buffs = time.time()
                time.sleep(2)
