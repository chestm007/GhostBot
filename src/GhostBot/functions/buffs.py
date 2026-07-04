"""Buff -- UNDER RECONSTRUCTION (reset on 2026-05-26). For now DOES nothing."""
from __future__ import annotations

import time

from GhostBot.functions.runner import Runner


class Buffs(Runner):
    def __init__(self, client):
        super().__init__(client)

    def _run(self) -> bool:
        # inert stub -- does nothing (no busy-loop)
        time.sleep(1)
        return True
