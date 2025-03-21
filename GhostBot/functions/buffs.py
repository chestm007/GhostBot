from __future__ import annotations

import time

from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.functions.runner import Runner
from GhostBot.lib import vk_codes

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


class Buffs(Runner):

    def __init__(self, client: ExtendedClient):
        super().__init__(client)
        self._last_time_used_buffs = 0

    def run(self) -> None:
        if time.time() - self._last_time_used_buffs > 60 * self._client.config.buff_interval:
            logger.info(f'{self._client.name}: Buffing.')
            for buff in self._client.config.bindings.get('buffs'):
                self._client.press_key(vk_codes[buff])
                self._last_time_used_buffs = time.time()
                time.sleep(2)
