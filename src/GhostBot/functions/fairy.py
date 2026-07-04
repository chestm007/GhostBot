"""Fairy -- Helper Mode (cross-PC): follows and heals the 1st GROUP MEMBER (the ally).

Flow each cycle (all BACKSTAGE -- does NOT move real mouse):
  - select ally = click on 1st group member portrait (team_1);
  - heal ally -> WAIT for cast (gap, to not cut the cast) -> P (follow);
  - periodic buff (at interval): combo on ally -> gap -> P;
  - AUTO-HEAL: if OWN Fairy HP drops below heal_self_threshold
    (default 50%): F1 (auto-target) -> heal -> gap -> click 1st member -> P.

Confirmed live (2026-05-26): F1 selects own Fairy; the bot's left_click
(SendMessage) selects the group member without moving the mouse. Portrait
coords in lib/talisman_ui_locations (team_1..team_4, ~81px spacing).
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from GhostBot.functions.runner import Runner
from GhostBot.lib.talisman_ui_locations import UI_locations

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow
    from GhostBot.config import FairyConfig


class Fairy(Runner):
    def __init__(self, bot_controller, client: "BotClientWindow"):
        super().__init__(client)
        self.config: FairyConfig = client.config.fairy
        self._bot_controller = bot_controller
        self._last_buff_time = 0  # timestamp of last buff cycle (0 = never)

    def _run(self) -> bool:
        if not self.config.helper_mode:
            self._client.set_action("🧚 Fairy idle (turn on Helper Mode)")
            return True
        return self._run_helper()

    def _run_helper(self) -> bool:
        follow = (self.config.bindings or {}).get('follow') or 'p'
        heal = (self.config.bindings or {}).get('heal')
        gap = float(self.config.heal_interval_secs or 3)  # cast + pause before P

        # AUTO-HEAL: if HER HP dropped, heal herself first.
        # Flow (owner's request): F1 -> heal -> wait for cast -> click 1st member -> P.
        # (F1 removes ally selection, hence re-select 1st member at the end).
        if self._self_hp_low():
            self._client.set_action("💖 Auto-heal (Low HP)")
            self._log_info('Helper: auto-heal (Low HP) -> F1 + heal')
            self._client.press_key('f1')        # F1 = selects own Fairy
            time.sleep(0.3)
            if heal:
                self._client.press_key(heal)
            time.sleep(gap)                      # wait for heal cast
            self._select_ally()                  # back to aiming ally (1st member)
            self._client.press_key(follow)
            self._client.set_action("🏃 Following ally (P)")
            return True

        # Select ally = 1st group member (click backstage on portrait).
        # Ensures aim each cycle (robust, and recovers after auto-heal).
        self._select_ally()

        # Periodic buff on ally: combo -> pause (last buff cast) -> P
        if self._should_buff():
            self._client.set_action("✨ Buffing ally")
            self._log_info('Helper: buffing ally...')
            for key, delay_ms in (self.config.buffs or []):
                if not self._client.running:
                    return True
                self._client.press_key(key)
                time.sleep(int(delay_ms) / 1000)
            time.sleep(gap)
            self._client.press_key(follow)
            self._client.set_action("🏃 Following ally (P)")
            self._last_buff_time = time.time()
            return True

        # Ally heal: press heal -> WAIT for cast (gap) -> P (without cutting the cast).
        self._client.set_action("💚 Healing ally")
        if heal:
            self._client.press_key(heal)
        time.sleep(gap)
        self._client.press_key(follow)
        self._client.set_action("🏃 Following ally (P)")
        return True

    def _select_ally(self) -> None:
        """Select ally = 1st group member, clicking on portrait (team_1).
        BACKSTAGE (SendMessage via left_click, does NOT move real mouse). Confirmed live
        that bot's left_click selects the group member."""
        self._client.left_click(UI_locations.team_1)
        time.sleep(0.2)

    def _self_hp_low(self) -> bool:
        """True if OWN Fairy HP dropped below auto-heal limit
        (FairyConfig.heal_self_threshold; default 50%). Accepts 0-1 or 0-100."""
        thr = self.config.heal_self_threshold
        thr = float(thr) if thr is not None else 0.5
        if thr > 1:            # UI sometimes sends 0-100 instead of 0.0-1.0
            thr = thr / 100
        try:
            return self._client.hp_percent < thr
        except Exception:
            return False

    def _should_buff(self) -> bool:
        """True if there are configured buffs AND enough time has passed since last buff."""
        if not self.config.buffs or not self.config.buff_interval_mins:
            return False
        interval_s = int(self.config.buff_interval_mins) * 60
        return (time.time() - self._last_buff_time) >= interval_s
