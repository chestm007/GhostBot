from __future__ import annotations

import time

from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.functions.runner import Locational
from GhostBot.lib.talisman_ui_locations import TeamLocations

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


class Fairy(Locational):

    _team_members: dict[int, ExtendedClient] = {}

    def __init__(self, bot_controller, client: ExtendedClient):
        super().__init__(client)
        self._bot_controller = bot_controller

    def run(self) -> bool:
        if len(self._team_members) == 0:
            if not self._detect_team_members():
                self._team_members = {}
                return False

        for i, member in self._team_members.items():
            if member.hp_percent < self._client.config.fairy.get('heal_at', 80):
                logger.debug(f'{self._client.name}: Weak member {member.name} {member.hp_percent}')
                while member.hp_percent < 1:
                    self._client.left_click(TeamLocations[i])
                    self._client.press_key(self._client.config.bindings.get('heal'))
                    self._client.bot_status_string = member.hp_percent
                logger.debug(f'{self._client.name}:  {member.name}: healed')

        if self._client.hp_percent < self._client.config.fairy.get('heal_self_at', 80):
            self._client.left_click(TeamLocations[0])
            self._client.press_key(self._client.config.bindings.get('heal'))
            logger.debug(f'{self._client.name}: heal self')
        self._goto_start_location()
        return True

    def _detect_team_members(self) -> bool:
        """
        :returns True if team members detected successfully, Falsey otherwise
        """
        self._team_members = {i: self._bot_controller.clients.get(name) for i, name in enumerate(self._client.team_members)}
        return self._team_members is not None

    def __detect_team_members(self):
        """
        Old func, shouldnt be needed
        :return:
        """
        self._client.target_self()
        time.sleep(0.2)
        if self._client.target_name != self._client.name:
            logger.debug(f'{self._client.name}: self not found??')
            return False
        for member_number in self._client.config.fairy.get('team'):

            # TODO: we know the memory addresses now, lets just try and use them, fallback to
            #       manual detection if we have too
            self._client.left_click(TeamLocations[member_number])
            time.sleep(0.2)
            self._team_members[member_number] = self.clients.get(self._client.target_name)
        logger.debug(f'{self._client.name}: Team: {" | ".join([m.name for m in self._team_members.values()])}')
        return True
