from __future__ import annotations

import time

from typing import TYPE_CHECKING

from GhostBot.functions.runner import Locational, InjectedLoggingMixin
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


class Attack(Locational):
    """
    returns True when mob killed or not found

    otherwise returns Falsey
    """
    _cur_attack_queue = []
    def __init__(self, client: BotClientWindow):
        super().__init__(client)
        self.config: AttackConfig = client.config.attack
        try:
            self._stuck_interval = int(self.config.stuck_interval or 10)
            self.roam_distance = int(self.config.roam_distance or 40)
        except AttributeError as e:
            self._log_err(f"{self._client.name} error {e}")
            self._stuck_interval = 10

    def _run(self) -> bool:
        self._client.close_inventory()
        self._client.dismount()

        context = AttackContext(self._client, self._stuck_interval)

        # if were too far away from our start location, move back there
        # So volta pro spot se passar do limite de aceitacao (ACCEPT_DISTANCE=100).
        # Dentro disso (mesmo um pouco acima do roam) ele aceita e segue atacando.
        if linear_distance(self.start_location, self._client.location) > self.ACCEPT_DISTANCE:
            self._log_debug(f'too far go back C:{self._client.location} | T:{self.start_location}')
            self._client.set_action("🏃 Voltando ao spot")
            with self._client.mounted():          # monta pra viajar mais rapido
                self._goto_start_location()        # volta pelo MAPA (com clique-isca)
            self._client.new_target()
            return True

        if not self._client.has_alive_target:# or (self._distance_to_target() or 0) > self.roam_distance:
            self._client.set_action("🔍 Procurando alvo")
            self._client.new_target()
            return True

        self._client.set_action(f"⚔️ Atacando {self._client.target_name or 'alvo'}")
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

    @staticmethod
    def _as_decimal(threshold) -> float:
        # UI accepts 0-100 (percent). If >1, treat as percent and convert.
        v = float(threshold)
        return v / 100 if v > 1 else v

    def _battle_pots(self):
        if self.config.bindings is None:
            return

        # MP pot
        mp_key = self.config.bindings.get('battle_mana_pot')
        mp_thr = self.config.battle_mana_threshold
        if mp_key is not None and mp_thr is not None:
            if self._client.mana_percent < self._as_decimal(mp_thr):
                self._client.press_key(mp_key)
                self._wait_resource_refill("MP")

        # HP pot
        hp_key = self.config.bindings.get('battle_hp_pot')
        hp_thr = self.config.battle_hp_threshold
        if hp_key is not None and hp_thr is not None:
            if self._client.hp_percent < self._as_decimal(hp_thr):
                self._client.press_key(hp_key)
                self._wait_resource_refill("HP")

    def _wait_resource_refill(self, resource: str, full_pct: float = 0.95, timeout_s: int = 30):
        """Apos usar pot, espera HP/MP encher antes de voltar a atacar.
        Atacar interrompe o regen do pot, entao precisa parar.
        Interrompe se: cheio (>= full_pct), HP caindo (sob ataque), ou timeout."""
        self._log_debug(f'{resource} baixo, usou pot. Aguardando recuperar...')
        start = time.time()
        last_pct = self._get_resource_pct(resource)
        while self._client.running and (time.time() - start) < timeout_s:
            time.sleep(0.5)
            current = self._get_resource_pct(resource)
            if current >= full_pct:
                self._log_debug(f'{resource} cheio ({current:.0%}), retomando ataque')
                return
            # se HP caiu significativamente, sob ataque -> nao adianta esperar
            if resource == "HP" and current < last_pct - 0.05:
                self._log_info(f'HP caiu durante regen ({last_pct:.0%} -> {current:.0%}), retomando pra defender')
                return
            last_pct = current
        self._log_debug(f'Timeout esperando {resource} encher ({timeout_s}s), seguindo')

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
