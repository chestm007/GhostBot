from __future__ import annotations

import time

from typing import TYPE_CHECKING

from GhostBot.config import BuffConfig
from GhostBot.functions.runner import Runner, run_at_interval
from GhostBot.lib.math import seconds

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


@run_at_interval()
class Buffs(Runner):

    def __init__(self, client: ExtendedClient):
        super().__init__(client)
        self.config: BuffConfig = client.config.buff
        self._interval = seconds(minutes=int(self.config.interval))

    def _run(self) -> None:
        self._log_info(f'Buffing.')
        for _key, _sleep in self.config.buffs:
            self._client.press_key(_key)
            time.sleep(seconds(seconds=_sleep))
