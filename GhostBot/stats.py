from dataclasses import dataclass

from GhostBot.controller.bot_controller import BotClientWindow
from GhostBot.functions import Runner


@dataclass
class Stats:

    def __init__(self, client: BotClientWindow):
        self._client = client
        self.kills: int = 0
        self.xp_gained: int = 0
        self.time_running: int = 0
        self.pet_feed_countdown: int = 0
        self.buffs_countdown: int = 0

    def refresh(self, function: Runner | None) -> None:
        if function is None: ...

    @property
    def pet_spawn_countdown(self) -> int:
        raise NotImplementedError
