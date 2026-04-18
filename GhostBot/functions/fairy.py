from __future__ import annotations

import time
from typing import TYPE_CHECKING

from GhostBot.functions.runner import Locational
from GhostBot.lib.math import linear_distance
from GhostBot.lib.talisman_ui_locations import TeamLocations

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow
    from GhostBot.config import FairyConfig


class Fairy(Locational):

    _team_members: dict[int, BotClientWindow] = {}

    def __init__(self, bot_controller, client: BotClientWindow):
        super().__init__(client)
        self.config: FairyConfig = client.config.fairy
        self._bot_controller = bot_controller

    def _run(self) -> bool:
        if self._client.hp_percent < float(self.config.heal_self_threshold):
            self._heal_self()
        for index, member in sorted(self._detect_team_members().items(), key=lambda i: i[1].hp_percent, reverse=True):
            if member.hp_percent < float(self.config.heal_team_threshold) and linear_distance(self._client.location, member.location) < 20:
                self._heal_team_member(index, member)

        self._goto_start_location()
        return True

    def _heal_self(self):
        while self._client.hp_percent < 0.9:
            if self._client.hp_percent < float(self.config.heal_self_threshold):
                self._log_info(f'Healing self...')
                self._client.left_click(TeamLocations[0])
                self._client.press_key(self.config.bindings.get('heal'))

    def _heal_team_member(self, index: int, member: BotClientWindow):
        self._log_info(f'Healing Weak member {member.name}')
        while member.hp_percent < 0.9 and self._client.running:
            self._client.dismount()
            self._client.close_inventory()
            self._client.left_click(TeamLocations[index + 1])
            self._client.press_key(self.config.bindings.get('heal'))
            time.sleep(0.5)
        self._log_debug(f'{member.name}: healed')

    def _detect_team_members(self) -> dict[int, BotClientWindow]:
        """
        :return: a dict of {index: ExtendedClient} representing the current team members.
        """
        return {
            k: v for k, v in {
                i: self._bot_controller.clients.get(name) for i, name in enumerate(self._client.team_members)
            }.items() if v and not v.disconnected
        }
