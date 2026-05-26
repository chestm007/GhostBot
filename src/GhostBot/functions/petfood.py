"""Pet -- EM RECONSTRUCAO (zerado em 2026-05-26). Por enquanto NAO faz nada."""
from __future__ import annotations

import time

from GhostBot.functions.runner import Runner


class Petfood(Runner):
    def __init__(self, client):
        super().__init__(client)

    def _run(self) -> bool:
        # stub inerte -- nao faz nada (sem busy-loop)
        time.sleep(1)
        return True
