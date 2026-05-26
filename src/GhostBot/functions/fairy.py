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
        self._last_buff_time = 0  # timestamp do último ciclo de buff (0 = nunca buffou)
        self._last_heal_time = 0  # Helper: timestamp da última cura

    def _run(self) -> bool:
        if self.config.helper_mode:
            return self._run_helper()
        if self._client.hp_percent < float(self.config.heal_self_threshold):
            self._heal_self()
        for index, member in sorted(self._detect_team_members().items(), key=lambda i: i[1].hp_percent, reverse=True):
            if member.hp_percent < float(self.config.heal_team_threshold) and linear_distance(self._client.location, member.location) < 20:
                self._heal_team_member(index, member)

        # Buff de time periodico
        if self._should_buff_team():
            self._buff_team()

        self._goto_start_location()
        return True

    def _run_helper(self) -> bool:
        """Modo Helper (cross-PC): cura + segue UM aliado so por TECLA, sem detectar.
        Loop: a cada heal_interval_secs aperta a tecla de cura + P (segue); no intervalo
        de buff aperta o combo de buffs + P. SEMPRE termina com P pra nao perder o follow.
        O usuario seleciona o char Helper na lista e da Start; o jogo segue o alvo dele."""
        follow = (self.config.bindings or {}).get('follow') or 'p'
        heal = (self.config.bindings or {}).get('heal')
        interval = int(self.config.heal_interval_secs or 2)
        now = time.time()

        # Cura periodica + P (mantem o follow)
        if now - self._last_heal_time >= interval:
            if heal:
                self._client.press_key(heal)
            self._client.press_key(follow)
            self._last_heal_time = now

        # Buff periodico + P
        if self._should_buff_team():
            self._log_info('Helper: buffando aliado...')
            for key, delay_ms in (self.config.buffs or []):
                if not self._client.running:
                    return True
                self._client.press_key(key)
                time.sleep(int(delay_ms) / 1000)
            self._client.press_key(follow)
            self._last_buff_time = time.time()

        time.sleep(0.3)   # evita busy-loop (timing da cura fica preciso a ~0.3s)
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

    def _should_buff_team(self) -> bool:
        """True se config tem buffs configurados E ja passou o intervalo desde o ultimo buff."""
        if not self.config.buffs:
            return False
        if not self.config.buff_interval_mins:
            return False
        interval_s = int(self.config.buff_interval_mins) * 60
        return (time.time() - self._last_buff_time) >= interval_s

    def _buff_team(self):
        """Aplica o combo de buffs em cada membro do time. Opcional: tambem na propria Fairy."""
        members = self._detect_team_members()
        if not members:
            self._log_debug('sem membros do time pra buffar')
            self._last_buff_time = time.time()  # nao tenta de novo no proximo tick
            return

        self._log_info(f'Buffando {len(members)} membro(s) do time...')
        self._client.dismount()
        self._client.close_inventory()

        for index, member in sorted(members.items()):
            self._buff_one(index + 1, member.name)

        if self.config.buff_self:
            self._buff_one(0, self._client.name)

        self._last_buff_time = time.time()
        self._log_info('Buff de time concluido.')

    def _buff_one(self, ui_index: int, target_name: str):
        """Clica no portrait (ui_index) e aplica cada buff do combo."""
        if not self._client.running:
            return
        self._log_debug(f'buffando {target_name} (ui_index={ui_index})')
        try:
            self._client.left_click(TeamLocations[ui_index])
        except (KeyError, IndexError):
            self._log_err(f'sem TeamLocations[{ui_index}], pulando {target_name}')
            return

        for key, delay_ms in self.config.buffs:
            if not self._client.running:
                return
            self._client.press_key(key)
            time.sleep(int(delay_ms) / 1000)
