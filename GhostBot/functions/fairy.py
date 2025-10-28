from __future__ import annotations

from typing import TYPE_CHECKING

from GhostBot.config import FairyConfig
from GhostBot.functions.runner import Locational
from GhostBot.lib.talisman_ui_locations import TeamLocations

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


class Fairy(Locational):

    _team_members: dict[int, ExtendedClient] = {}

    def __init__(self, bot_controller, client: ExtendedClient):
        super().__init__(client)
        self.config: FairyConfig = client.config.fairy
        self._bot_controller = bot_controller

    def _run(self) -> bool:
        if len(self._team_members) == 0:
            if not self._detect_team_members():
                self._team_members = {}
                return False

        for i, member in self._team_members.items():
            if member.hp_percent < self.config.heal_team_threshold:
                self._log_debug(f'Weak member {member.name} {member.hp_percent}')
                while member.hp_percent < 0.9 and self._client.running:
                    self._client.left_click(TeamLocations[i+1])
                    self._client.press_key(self.config.bindings.get('heal'))
                self._log_debug(f'{member.name}: healed')

        if self._client.hp_percent < self.config.heal_self_threshold:
            self._client.left_click(TeamLocations[0])
            self._client.press_key(self.config.bindings.get('heal'))
            self._log_debug(f'heal self')
        self._goto_start_location()
        return True

    def _detect_team_members(self) -> bool:
        """
        :return: True if team members detected successfully, Falsey otherwise
        """
        self._team_members = {i: self._bot_controller.clients.get(name) for i, name in enumerate(self._client.team_members)}
        return self._team_members is not None
