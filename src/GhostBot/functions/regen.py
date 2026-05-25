from __future__ import annotations

import time
from typing import TYPE_CHECKING

from GhostBot.functions.runner import Locational
from GhostBot.lib.math import seconds

if TYPE_CHECKING:
    from GhostBot.config import RegenConfig
    from GhostBot.controller.bot_controller import BotClientWindow


class Regen(Locational):
    MAX_REGEN_SECS = 60  # rede de seguranca: nunca senta mais que isso sem recuperar -> volta a atacar

    def __init__(self, client: BotClientWindow, fairy_activated: bool = False):
        super().__init__(client=client)

        self._fairy_activated = fairy_activated
        self.config: RegenConfig = self._client.config.regen
        self._mana_threshold = self._normalize_threshold(self.config.mana_threshold, default=0.75)
        self._hp_threshold = self._normalize_threshold(self.config.hp_threshold, default=0.75)
        # classes sem mana (ex: Assassin) ignoram o MP no descanso
        self._ignore_mana = bool(getattr(self.config, 'ignore_mana', False))
        # volta a atacar ao recuperar ACIMA do limite (com folga); nunca exige 100% -> evita sentar pra sempre
        self._hp_recovered = min(self._hp_threshold + 0.15, 0.95)
        self._mana_recovered = min(self._mana_threshold + 0.15, 0.95)

    @staticmethod
    def _normalize_threshold(value, default: float) -> float:
        v = float(value if value is not None else default)
        # UI accepts 0-100 (percent). If user entered >1, treat as percent and convert.
        return v / 100 if v > 1 else v

    def _run(self) -> bool:
        """
        :return: True is we healed successfully, False if we were attacked, or in battle while healing
        """
        if self._mana_low() or self._hp_low():
            self._client.set_action("🪑 Descansando (HP/MP)")
            self._goto_start_location()

            start_wait = time.time()
            if self._client.in_battle:
                while self._client.in_battle and time.time() - start_wait < seconds(seconds=3):
                    time.sleep(0.5)
                    if not self._client.in_battle:
                        break
                else:
                    return False
            self._log_info(f'low hp/mana, starting Regen')

            if self.config.bindings:
                # mana/hp pots\
                self._use_hp_pot()
                self._use_mana_pot()

            hp = int(self._client.hp)
            regen_start = time.time()
            while not self._recovered() and self._client.running:
                self._log_debug(f'healing')
                time.sleep(2)
                if self._client.in_battle or self._client.hp < hp:
                    self._log_debug(f'Ouch, attacking')
                    return False
                if time.time() - regen_start > self.MAX_REGEN_SECS:
                    self._log_info('Regen demorou demais (%ss sem recuperar), voltando a atacar', self.MAX_REGEN_SECS)
                    break
                self._goto_spot_and_sit()
                hp = int(self._client.hp)
            return True
        return False

    def _recovered(self) -> bool:
        """Recuperou o suficiente pra voltar a atacar (acima do limite, com folga).
        Fairy ignora HP; classe sem mana ignora MP -> nunca espera recurso que nao enche."""
        hp_ok = self._fairy_activated or (self._client.hp_percent >= self._hp_recovered)
        mana_ok = self._ignore_mana or (self._client.mana_percent >= self._mana_recovered)
        return hp_ok and mana_ok

    def _mana_low(self) -> int:
        if self._ignore_mana:
            return False
        return self._client.mana_percent < self._mana_threshold

    def _hp_low(self) -> int:
        if self._fairy_activated:
            return False
        return self._client.hp_percent < self._hp_threshold

    def _use_hp_pot(self) -> None:
        if self._client.hp_percent < self._hp_threshold:
            if self.config.bindings.get('hp_pot') is not None:
                self._goto_spot_and_sit()
                self._client.press_key(self.config.bindings.get('hp_pot'))

    def _use_mana_pot(self) -> None:
        if self._ignore_mana:
            return
        if self._client.mana_percent < self._mana_threshold:
            if self.config.bindings.get('mana_pot') is not None:
                self._goto_spot_and_sit()
                self._client.press_key(self.config.bindings.get('mana_pot'))

    def _goto_spot_and_sit(self) -> None:
        self._goto_start_location()
        self._sit()

    def _sit(self):
        if not self._client.sitting:
            self._log_debug(f'sitting')
            self._client.sit(self.config.bindings.get('sit'))
