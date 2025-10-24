from __future__ import annotations

import time

from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.config import BuffConfig
from GhostBot.functions.runner import Runner
from GhostBot.lib.math import seconds

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


class Buffs(Runner):

    def __init__(self, client: ExtendedClient):
        super().__init__(client)
        self.config: BuffConfig = client.config.buff
        self._last_time_used_buffs = 0

    def _run(self) -> None:
        if time.time() - self._last_time_used_buffs > seconds(minutes=int(self.config.interval)):
            logger.info(f'{self._client.name}: Buffing.')
            for _key, _sleep in self.config.buffs:
                self._client.press_key(_key)
                self._last_time_used_buffs = time.time()
                time.sleep(int(_sleep) / 1000)
