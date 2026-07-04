from __future__ import annotations

import time
from typing import TYPE_CHECKING

from GhostBot.functions.runner import Locational
from GhostBot.lib.math import seconds

if TYPE_CHECKING:
    from GhostBot.config import RegenConfig
    from GhostBot.controller.bot_controller import BotClientWindow


class Regen(Locational):
    MAX_REGEN_SECS = 16  # safety net: never rests longer than this -> back to attacking

    def __init__(self, client: BotClientWindow, fairy_activated: bool = False):
        super().__init__(client=client)

        self._fairy_activated = fairy_activated
        self.config: RegenConfig = self._client.config.regen
        self._mana_threshold = self._normalize_threshold(self.config.mana_threshold, default=0.75)
        self._hp_threshold = self._normalize_threshold(self.config.hp_threshold, default=0.75)
        # classes without mana (e.g. Assassin) ignore MP during rest
        self._ignore_mana = bool(getattr(self.config, 'ignore_mana', False))
        # Recover to ~FULL before resuming attack (do not waste pot raising
        # to 85%). MAX_REGEN_SECS timeout (60s) prevents sitting forever if it does not fill.
        self._hp_recovered = 0.95
        self._mana_recovered = 0.95

    @staticmethod
    def _normalize_threshold(value, default: float) -> float:
        v = float(value if value is not None else default)
        # UI accepts 0-100 (percent). If user entered >1, treat as percent and convert.
        return v / 100 if v > 1 else v

    def _run(self) -> bool:
        """:return: True if rested/resumed ok; False if attacked or continues in combat.

        Order (owner's request): 1) NEVER rest/return to spot in COMBAT -> wait
        to exit; 2) RECOVER first (pot + sit AT CURRENT LOCATION); 3) only AFTER
        recovered, and out of combat, return to spot."""
        if not (self._mana_low() or self._hp_low()):
            return False

        self._client.set_action("🪑 Resting (HP/MP)")

        # 1) In combat? Wait to exit. If does not exit, let Attack/battle_pots handle
        # and try again in next cycle (DO NOT sit or return to spot in combat).
        if self._client.in_battle:
            start_wait = time.time()
            while self._client.in_battle and time.time() - start_wait < seconds(seconds=3):
                time.sleep(0.5)
            if self._client.in_battle:
                return False

        self._log_info('low hp/mana, starting Regen')

        # 2) RECOVER FIRST -- pot + sit WHERE IT IS (does not go to spot yet)
        if self.config.bindings:
            self._use_hp_pot()
            self._use_mana_pot()
        hp = int(self._client.hp)
        regen_start = time.time()
        while not self._recovered() and self._client.running:
            # ATTACK PRIORITY: if entered combat (aggressive mob came close) or
            # is getting beaten, STOP resting and resume attacking immediately.
            if self._client.in_battle or int(self._client.hp) < hp:
                self._log_debug('Ouch -> resume attacking')
                return False
            if time.time() - regen_start > self.MAX_REGEN_SECS:
                self._log_info('Regen reached limit (%ss), continuing', self.MAX_REGEN_SECS)
                break
            self._sit()  # sits WHERE IT IS (does not go to spot)
            hp = int(self._client.hp)
            # rest in short steps checking combat -> fast response to aggressive mob
            for _ in range(3):
                time.sleep(0.5)
                if self._client.in_battle:
                    self._log_debug('Aggressive mob during rest -> resume attacking')
                    return False

        # 3) RECOVERED -> stand up and ONLY THEN return to spot (only out of combat)
        self._stand()
        if not self._client.in_battle:
            self._client.set_action("🏃 Returning to spot")
            self._goto_start_location()
        return True

    def _recovered(self) -> bool:
        """Recovered enough to resume attacking (above threshold, with margin).
        Fairy ignores HP; class without mana ignores MP -> never waits for resource that does not fill."""
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
        # pot works STANDING and WHERE IT IS (does not go to spot) -- recover first.
        # _use_pot has cooldown (16s) to not re-pot before previous pot acts.
        if self._client.hp_percent < self._hp_threshold:
            key = self.config.bindings.get('hp_pot')
            if key is not None:
                self._use_pot(key)

    def _use_mana_pot(self) -> None:
        if self._ignore_mana:
            return
        if self._client.mana_percent < self._mana_threshold:
            key = self.config.bindings.get('mana_pot')
            if key is not None:
                self._use_pot(key)

    def _goto_spot_and_sit(self) -> None:
        self._goto_start_location()
        self._sit()

    def _sit(self):
        if not self._client.sitting:
            self._log_debug(f'sitting')
            self._client.sit(self.config.bindings.get('sit'))

    def _stand(self):
        """Stands up (if sitting) before resuming walking/attacking. sit() does toggle."""
        if self._client.sitting:
            self._log_debug('standing up')
            self._client.sit(self.config.bindings.get('sit'))
