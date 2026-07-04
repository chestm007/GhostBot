from __future__ import annotations

import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow


class TargetLockMixin:
    _client: "BotClientWindow"
    @staticmethod
    def _as_decimal(threshold) -> float:
        """UI accepts 0-100 (percent). If >1, treat as percent and convert."""
        v = float(threshold)
        return v / 100 if v > 1 else v

    def _target_is_boss(self, boss: str) -> bool:
        """True if current target is alive and name matches (contains) the boss."""
        if not self._client.has_alive_target:
            return False
        tname = (self._client.target_name or '').lower()
        return bool(tname) and boss.lower() in tname

    def _find_boss(self, boss: str, attempts: int = 10, pause_s: float = 0.3) -> bool:
        """TAB until target is the boss. True if found, False if not appeared."""
        for _ in range(attempts):
            if not self._client.running:
                return False
            self._client.new_target()
            time.sleep(pause_s)
            if self._target_is_boss(boss):
                return True
        return False
