from __future__ import annotations

import time

from typing import TYPE_CHECKING

from GhostBot.functions.combat_helpers import TargetLockMixin
from GhostBot.functions.runner import Locational, InjectedLoggingMixin, POT_DURATION_SECS
from GhostBot.lib.math import linear_distance

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow
    from GhostBot.config import AttackConfig


class AttackContext(InjectedLoggingMixin):
    """
    Object to track changes between now ald last check.

    If it detects a change, it will return true, then set the current values to what it read, and return
    false until they change again
    """
    def __init__(self, client: BotClientWindow, stuck_interval: int) -> None:
        super().__init__(client)
        self._location = self._location = tuple(self._client.location)
        self._target_hp = self._client.target_hp
        self._last_changed_time = time.time()
        self._stuck_interval = stuck_interval
        #self._check_stuck = self._client.config.unstuck

    @property
    def location_changed(self) -> bool:
        loc = tuple(self._location)
        if linear_distance(loc, self._client.location) > 1:
            self._location = self._client.location
            self._log_debug('location changed')
            return True
        return False

    @property
    def target_hp_changed(self) -> bool:
        if self._target_hp != self._client.target_hp:
            self._target_hp = self._client.target_hp
            self._log_debug('target hp changed')
            return True
        return False

    @property
    def stuck(self) -> bool:
        # if not self._check_stuck:
        #     return False

        # if target HP or our position changed, we're not stuck
        if self.location_changed or self.target_hp_changed:
            self._log_debug('target_hp or location changed, unstuck')
            self._last_changed_time = time.time()
            return False

        # if target hp and our position haven't changed in `stuck_interval` we're stuck
        if time.time() - self._last_changed_time > self._stuck_interval:
            self._log_debug(f'target_hp and location unchanged in {self._stuck_interval}s, stuck')
            self._last_changed_time = time.time()
            return True

        # targethp and location haven't changed, but we aren't past `stuck_interval` we're not stuck
        self._log_debug('target_hp or location changed and not past self._stuck_interval, unstuck')
        return False


class Attack(TargetLockMixin, Locational):
    """
    returns True when mob killed or not found

    otherwise returns Falsey
    """
    _cur_attack_queue = []
    RETURN_DONE_DISTANCE = 15   # 'arrived' at spot (exits return mode) within this range
    MAX_RETURN_CYCLES = 6       # cycles trying to return before accepting and farming here (anti-stuck)

    def __init__(self, client: BotClientWindow):
        super().__init__(client)
        self.config: AttackConfig = client.config.attack
        # Farm class: 'dps' (default) | 'tamer' (commands pet) | 'fairy' (heals, no HP pot)
        self._char_class = (getattr(self.config, 'char_class', None) or 'dps').strip().lower()
        try:
            self._stuck_interval = int(self.config.stuck_interval or 10)
            self.roam_distance = int(self.config.roam_distance or 40)
        except AttributeError as e:
            self._log_err(f"{self._client.name} error {e}")
            self._stuck_interval = 10
            self.roam_distance = 40
        self._returning = False     # 'returning to spot' mode: persists until ARRIVING
        self._return_cycles = 0
        self._last_buff_time = 0    # periodic buffs (came from the defunct Buff tab)

    def _run(self) -> bool:
        self._client.close_inventory()
        self._client.dismount()
        self._maybe_buff()   # periodic buffs (every buff_interval_mins)

        context = AttackContext(self._client, self._stuck_interval)

        # RETURN MODE: passed max radius ('Max distance from spot') -> enters return mode.
        # Only EXITS when ARRIVING close to the spot -- so a mob on the path does NOT cancel
        # the trip (before it would stop mid-path to farm). Anti-stuck: gives up after
        # MAX_RETURN_CYCLES (e.g. mob permanently blocking) and farms where it is.
        dist = linear_distance(self.start_location, self._client.location)
        if dist > self.roam_distance:
            self._returning = True
        if self._returning:
            if dist <= self.RETURN_DONE_DISTANCE:
                self._returning = False            # arrived close to spot -> can farm
                self._return_cycles = 0
            else:
                self._return_cycles += 1
                if self._return_cycles > self.MAX_RETURN_CYCLES:
                    self._log_info("return to spot: did not arrive in %s cycles (blocked?), "
                                   "farming here", self.MAX_RETURN_CYCLES)
                    self._returning = False
                    self._return_cycles = 0
                else:
                    self._log_debug('returning to spot C:%s | T:%s', self._client.location, self.start_location)
                    self._client.set_action("🏃 Returning to spot")
                    self._goto_start_location()    # only TRAVELS; does not attack mobs on the path
                    return True

        # BOSS LOCK: attacks ONLY the boss (TAB until name matches). Ignores common mobs.
        if self.config.boss_lock and self.config.boss_name:
            return self._run_boss(self.config.boss_name.strip())

        if not self._client.has_alive_target:# or (self._distance_to_target() or 0) > self.roam_distance:
            self._client.set_action("🔍 Looking for target")
            self._client.new_target()
            return True

        self._client.set_action(f"⚔️ Attacking {self._client.target_name or 'target'}")
        self._command_pet()   # Tamer: commands pet to attack this target (1x per mob)
        while self._client.target_hp is not None and self._client.target_hp >= 0 and self._client.running:
            if self._client.target_name == self._client.name:  # if were targeting ourselves, get a new target
                return True

            # battle pot logic
            self._battle_pots()

            if not self._cur_attack_queue:
                self._cur_attack_queue = list(self.config.attacks)

            key, interval = self._cur_attack_queue.pop(0)
            self._log_debug(f'ATTACK! {key}  -- {interval}s')
            self._client.press_key(key)
            time.sleep(int(interval) / 1000)

            if context.stuck:  # if we're stuck, get a new target and rerun.
                self._client.new_target()
                return True
        return False

    def _run_boss(self, boss: str) -> bool:
        """Boss mode: ensures target is the boss (TAB until found) and attacks ONLY it."""
        if not self._target_is_boss(boss):
            if not self._find_boss(boss):
                self._client.set_action(f"🔍 Looking for boss: {boss}")
                return True   # boss not appeared -> wait (do not hit common mob)
        self._client.set_action(f"👑 BOSS: {boss}")
        self._command_pet()   # Tamer: commands pet to attack the boss (1x per engagement)
        while self._client.target_hp is not None and self._client.target_hp >= 0 and self._client.running:
            if not self._target_is_boss(boss):
                return True   # target is no longer the boss -> re-find in next cycle
            self._battle_pots()
            if not self._cur_attack_queue:
                self._cur_attack_queue = list(self.config.attacks)
            key, interval = self._cur_attack_queue.pop(0)
            self._client.press_key(key)
            time.sleep(int(interval) / 1000)
        return True

    def _command_pet(self) -> None:
        """Tamer: presses pet attack key to command pet to attack current target.
        Called 1x when engaging target (the while loop keeps the mob until death) = 1 command per mob."""
        if self._char_class != 'tamer':
            return
        key = (self.config.bindings or {}).get('pet_attack')
        if key:
            self._client.press_key(key)

    def _maybe_buff(self) -> None:
        """Periodic buffs (came from the defunct Buff tab): every buff_interval_mins presses the
        buff combo. Auto-buff (applies to self), no target needed and not required to be out of combat."""
        buffs = self.config.buffs
        interval = self.config.buff_interval_mins
        if not buffs or not interval:
            return
        if time.time() - self._last_buff_time < int(interval) * 60:
            return
        self._client.set_action("✨ Buffing")
        for key, delay_ms in buffs:
            if not self._client.running:
                return
            self._client.press_key(key)
            time.sleep(int(delay_ms) / 1000)
        self._last_buff_time = time.time()

    def _battle_pots(self):
        if self.config.bindings is None:
            return

        # MP pot -- only pot if pot duration has passed (16s); otherwise the previous one is
        # still active (avoids duplicate pot). After potting, wait for it to act.
        mp_key = self.config.bindings.get('battle_mana_pot')
        mp_thr = self.config.battle_mana_threshold
        if mp_key is not None and mp_thr is not None:
            if self._client.mana_percent < self._as_decimal(mp_thr) and self._use_pot(mp_key):
                self._wait_resource_refill("MP")

        # HP: FAIRY heals itself (skill, instead of pot -- it does not use HP pot); DPS/Tamer
        # use HP pot (with 16s cooldown). MP follows pot for all (healing costs mana).
        hp_thr = self.config.battle_hp_threshold
        if hp_thr is not None and self._client.hp_percent < self._as_decimal(hp_thr):
            if self._char_class == 'fairy':
                heal_key = self.config.bindings.get('heal')
                if heal_key:
                    self._client.press_key(heal_key)   # heal is not pot -> no pot cooldown
                    self._wait_resource_refill("HP")
            else:
                hp_key = self.config.bindings.get('battle_hp_pot')
                if hp_key and self._use_pot(hp_key):
                    self._wait_resource_refill("HP")

    def _wait_resource_refill(self, resource: str, full_pct: float = 0.95, timeout_s: int = POT_DURATION_SECS):
        """After using pot, wait for HP/MP to fill before resuming attack.
        Attacking interrupts the pot's regen, so need to stop. The pot acts over
        ~POT_DURATION_SECS (16s) -- hence timeout = pot duration (wait to 'use the
        whole pot', unless it fills before).
        Interrupts if: full (>= full_pct), HP dropping (under attack), or timeout."""
        self._log_debug(f'{resource} low, used pot. Waiting to recover...')
        start = time.time()
        last_pct = self._get_resource_pct(resource)
        while self._client.running and (time.time() - start) < timeout_s:
            time.sleep(0.5)
            current = self._get_resource_pct(resource)
            if current >= full_pct:
                self._log_debug(f'{resource} full ({current:.0%}), resuming attack')
                return
            # if HP dropped significantly, under attack -> no point waiting
            if resource == "HP" and current < last_pct - 0.05:
                self._log_info(f'HP dropped during regen ({last_pct:.0%} -> {current:.0%}), resuming to defend')
                return
            last_pct = current
        self._log_debug(f'Timeout waiting for {resource} to fill ({timeout_s}s), continuing')

    def _get_resource_pct(self, resource: str) -> float:
        if resource == "HP":
            return self._client.hp_percent or 0
        elif resource == "MP":
            return self._client.mana_percent or 0
        return 0

    def _distance_to_target(self) -> int | None:
        if self._client.has_alive_target:
            if (tgt_loc := self._client.target_location) is not None:
                return linear_distance(self.start_location, tgt_loc)
        return None
