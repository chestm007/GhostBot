"""Cave Boss mode -- role per class (Tank / DPS / Fairy).

The "Boss" tab in the UI selects the role; this runner acts according to `config.boss.role`.
The 3 roles are implemented (2026-05-27):

- TANK: locks on boss (TAB until name matches), attacks with combo WITHOUT stopping, and every
  `buff_interval_secs` reapplies tank buffs (just presses the key; auto-cast, does not
  change target). HP/MP pots optional (empty key = off; tank leaves MP empty).
- DPS: hits the boss; if PULLS AGGRO (loses HP in combat -- we infer, cannot read
  boss aggro directly) retreats with F1 -> waits to exit combat -> tank re-pulls ->
  returns. Low MP: F1 -> waits to exit combat -> pot. Aggro always on.
- FAIRY: spam healing key on CURRENT TARGET every `heal_interval_secs`; the player
  changes the target (no auto-aiming -- cannot read other members' HP).

Reuses shared boss-lock logic from `GhostBot.functions.combat_helpers.TargetLockMixin`.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from GhostBot.functions.combat_helpers import TargetLockMixin
from GhostBot.functions.runner import Runner, POT_DURATION_SECS

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow
    from GhostBot.config import BossConfig


class Boss(TargetLockMixin, Runner):
    def __init__(self, client: "BotClientWindow"):
        super().__init__(client)
        self.config: BossConfig = client.config.boss
        self._cur_attack_queue: list = []
        self._last_buff_time = 0.0   # timestamp of last tank buff cycle

    def _run(self) -> bool:
        role = (self.config.role or '').strip().lower()
        if role == 'tank':
            return self._run_tank()
        if role == 'dps':
            return self._run_dps()
        if role == 'fairy':
            return self._run_fairy()
        self._client.set_action("🐉 Boss: select a Role in the tab")
        return True

    # ------------------------------------------------------------------- DPS
    def _run_dps(self) -> bool:
        """Hits the boss; if PULLS AGGRO (loses HP in combat) retreats: F1 -> waits to
        exit combat -> tank re-pulls -> returns. Same logic for low MP: F1 -> waits to
        exit combat -> pot. (Cannot read boss aggro directly; we infer from HP drop.)"""
        boss = (self.config.boss_name or '').strip()
        if not boss:
            self._client.set_action("🐉 DPS: configure Boss Name")
            return True

        # Low MP (before engaging) -> retreat and recover
        if self._mp_low():
            return self._recover_mp(boss)

        if not self._target_is_boss(boss):
            if not self._find_boss(boss):
                self._client.set_action(f"🔍 Looking for boss: {boss}")
                return True

        self._client.set_action(f"⚔️ DPS on boss: {boss}")
        last_hp = self._safe_hp()
        while self._client.target_hp is not None and self._client.target_hp >= 0 and self._client.running:
            if not self._target_is_boss(boss):
                return True
            # AGGRO: lost HP in combat -> pulled aggro -> retreat (F1) and wait for tank
            cur_hp = self._safe_hp()
            if last_hp is not None and cur_hp is not None and cur_hp < last_hp:
                return self._backoff_aggro(boss)
            last_hp = cur_hp
            # Low MP mid-fight -> retreat and recover
            if self._mp_low():
                return self._recover_mp(boss)
            self._hp_pot_simple()   # optional HP pot (empty key = off)
            if not self._cur_attack_queue:
                self._cur_attack_queue = list(self.config.attacks or [])
            if not self._cur_attack_queue:
                self._client.set_action("⚔️ DPS: configure Attack Combo")
                return True
            key, interval = self._cur_attack_queue.pop(0)
            self._client.press_key(key)
            time.sleep(int(interval) / 1000)
        return True

    def _backoff_aggro(self, boss: str) -> bool:
        """Pulled aggro: F1 (selects self -> stops attacking boss) -> waits to exit
        combat (tank re-pulls due to threat) -> TAB to re-grab boss -> resume hitting."""
        self._client.set_action("🛑 Pulled aggro -> F1, waiting for tank to re-pull")
        self._log_info("DPS: pulled aggro -> F1 + wait to exit combat")
        self._client.press_key('f1')
        self._wait_out_of_combat()
        self._find_boss(boss)   # TAB back to boss -> continues in next cycle
        return True

    def _recover_mp(self, boss: str) -> bool:
        """Low MP: F1 (stop attacking) -> waits to exit combat -> takes MP pot -> lets
        it rise a bit -> TAB to RE-GRAB target (owner's request) -> resume hitting. No pot
        configured, just retreats, waits and re-grabs."""
        self._client.set_action("💧 Low MP -> F1, recovering out of combat")
        self._log_info("DPS: Low MP -> F1 + recover")
        self._client.press_key('f1')
        self._wait_out_of_combat()
        mp_key = (self.config.bindings or {}).get('battle_mana_pot')
        if mp_key:
            self._use_pot(mp_key)   # only pot if not on cooldown (16s) -- avoids duplicate pot
            thr = self._as_decimal(self.config.battle_mana_threshold) if self.config.battle_mana_threshold is not None else 0.5
            # wait for MP to rise (retreated, not attacking -> pot acts). Up to pot duration.
            start = time.time()
            while self._client.running and (time.time() - start) < POT_DURATION_SECS:
                time.sleep(0.5)
                try:
                    if self._client.mana_percent >= thr:
                        break
                except Exception:
                    break
        self._find_boss(boss)   # TAB back to target -> resume hitting
        return True

    def _wait_out_of_combat(self, timeout_s: int = 20) -> None:
        """Waits for character to EXIT combat (tank re-pulled). Bounded by timeout and
        respects Stop (client.running)."""
        start = time.time()
        while self._client.running and self._client.in_battle and (time.time() - start) < timeout_s:
            time.sleep(0.5)

    def _mp_low(self) -> bool:
        thr = self.config.battle_mana_threshold
        if thr is None:
            return False
        try:
            return self._client.mana_percent < self._as_decimal(thr)
        except Exception:
            return False

    def _hp_pot_simple(self) -> None:
        """HP pot in combat (optional, blank = off). HP only -- DPS MP uses retreat.
        With cooldown (16s) to not re-pot while previous pot is still active."""
        hp_key = (self.config.bindings or {}).get('battle_hp_pot')
        hp_thr = self.config.battle_hp_threshold
        if hp_key and hp_thr is not None and self._client.hp_percent < self._as_decimal(hp_thr):
            self._use_pot(hp_key)

    def _safe_hp(self):
        try:
            return self._client.hp
        except Exception:
            return None

    # ----------------------------------------------------------------- FAIRY
    def _run_fairy(self) -> bool:
        """Heal on CURRENT TARGET (option 'a'): Fairy only spam the heal key; the player
        changes the target (clicks on who needs it). No aiming logic -- cannot read HP
        of other members. HP/MP pots for self are optional (empty key = off)."""
        heal = (self.config.bindings or {}).get('heal')
        if not heal:
            self._client.set_action("🧚 Fairy: configure Heal Key")
            return True
        self._battle_pots()   # takes care of OWN Fairy (HP/MP), if configured
        self._client.set_action("💚 Healing (current target)")
        self._client.press_key(heal)
        time.sleep(float(self.config.heal_interval_secs or 2))
        return True

    # ------------------------------------------------------------------ TANK
    def _run_tank(self) -> bool:
        boss = (self.config.boss_name or '').strip()
        if not boss:
            self._client.set_action("🐉 Tank: configure Boss Name")
            return True

        # ensures target is the boss (TAB until found)
        if not self._target_is_boss(boss):
            if not self._find_boss(boss):
                self._client.set_action(f"🔍 Looking for boss: {boss}")
                return True

        self._client.set_action(f"🛡️ TANK on boss: {boss}")
        while self._client.target_hp is not None and self._client.target_hp >= 0 and self._client.running:
            if not self._target_is_boss(boss):
                return True   # target is no longer the boss -> re-find in next cycle
            self._maybe_buff()
            # TANK does not pot on boss -- Fairies heal the tank (owner's decision).
            if not self._cur_attack_queue:
                self._cur_attack_queue = list(self.config.attacks or [])
            if not self._cur_attack_queue:
                self._client.set_action(f"🛡️ Tank: configure Attack Combo")
                return True   # no combo -> nothing to press
            key, interval = self._cur_attack_queue.pop(0)
            self._client.press_key(key)
            time.sleep(int(interval) / 1000)
        return True

    def _maybe_buff(self) -> None:
        """Reapplies tank buffs every buff_interval_secs (just presses the key --
        tank buff is auto-cast, does not change target)."""
        buffs = self.config.buffs or []
        interval = self.config.buff_interval_secs
        if not buffs or not interval:
            return
        if time.time() - self._last_buff_time < float(interval):
            return
        for key, delay_ms in buffs:
            if not self._client.running:
                return
            self._client.press_key(key)
            time.sleep(int(delay_ms) / 1000)
        self._last_buff_time = time.time()

    def _battle_pots(self) -> None:
        """OWN HP/MP pots, with cooldown (16s) to not re-pot. Used by FAIRY
        (her own pots). TANK does not call this -- Fairies heal the tank on boss.
        Optional: empty key = off."""
        b = self.config.bindings or {}

        mp_key = b.get('battle_mana_pot')
        mp_thr = self.config.battle_mana_threshold
        if mp_key and mp_thr is not None and self._client.mana_percent < self._as_decimal(mp_thr):
            self._use_pot(mp_key)

        hp_key = b.get('battle_hp_pot')
        hp_thr = self.config.battle_hp_threshold
        if hp_key and hp_thr is not None and self._client.hp_percent < self._as_decimal(hp_thr):
            self._use_pot(hp_key)
