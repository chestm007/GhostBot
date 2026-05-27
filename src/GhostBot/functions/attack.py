from __future__ import annotations

import time

from typing import TYPE_CHECKING

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


class Attack(Locational):
    """
    returns True when mob killed or not found

    otherwise returns Falsey
    """
    _cur_attack_queue = []
    RETURN_DONE_DISTANCE = 15   # 'centralizou' no spot (sai do modo voltar) dentro disso
    MAX_RETURN_CYCLES = 6       # ciclos tentando voltar antes de aceitar e farmar (anti-trava)

    def __init__(self, client: BotClientWindow):
        super().__init__(client)
        self.config: AttackConfig = client.config.attack
        # Classe pro farm: 'dps' (padrao) | 'tamer' (comanda o pet) | 'fairy' (se cura, sem pot HP)
        self._char_class = (getattr(self.config, 'char_class', None) or 'dps').strip().lower()
        try:
            self._stuck_interval = int(self.config.stuck_interval or 10)
            self.roam_distance = int(self.config.roam_distance or 40)
        except AttributeError as e:
            self._log_err(f"{self._client.name} error {e}")
            self._stuck_interval = 10
            self.roam_distance = 40
        self._returning = False     # modo 'voltando ao spot': persiste ate CENTRALIZAR
        self._return_cycles = 0

    def _run(self) -> bool:
        self._client.close_inventory()
        self._client.dismount()

        context = AttackContext(self._client, self._stuck_interval)

        # MODO 'VOLTANDO': passou do raio ('Distancia max do spot') -> entra no modo voltar.
        # So SAI quando CENTRALIZA perto do spot -- assim um mob no caminho NAO cancela a
        # viagem (antes ele parava no meio do caminho pra farmar). Anti-trava: desiste apos
        # MAX_RETURN_CYCLES (ex.: mob bloqueando de vez) e farma onde esta.
        dist = linear_distance(self.start_location, self._client.location)
        if dist > self.roam_distance:
            self._returning = True
        if self._returning:
            if dist <= self.RETURN_DONE_DISTANCE:
                self._returning = False            # chegou perto do spot -> pode farmar
                self._return_cycles = 0
            else:
                self._return_cycles += 1
                if self._return_cycles > self.MAX_RETURN_CYCLES:
                    self._log_info("voltar ao spot: nao centralizou em %s ciclos (bloqueado?), "
                                   "farmando aqui", self.MAX_RETURN_CYCLES)
                    self._returning = False
                    self._return_cycles = 0
                else:
                    self._log_debug('voltando ao spot C:%s | T:%s', self._client.location, self.start_location)
                    self._client.set_action("🏃 Voltando ao spot")
                    self._goto_start_location()    # so VIAJA; nao ataca mob no caminho
                    return True

        # BOSS LOCK: ataca SO o boss (da TAB ate o nome bater). Ignora mobs comuns.
        if self.config.boss_lock and self.config.boss_name:
            return self._run_boss(self.config.boss_name.strip())

        if not self._client.has_alive_target:# or (self._distance_to_target() or 0) > self.roam_distance:
            self._client.set_action("🔍 Procurando alvo")
            self._client.new_target()
            return True

        self._client.set_action(f"⚔️ Atacando {self._client.target_name or 'alvo'}")
        self._command_pet()   # Tamer: manda o pet atacar este alvo (1x por mob)
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

    def _target_is_boss(self, boss: str) -> bool:
        """True se o alvo atual esta vivo e o nome bate (contem) com o boss."""
        if not self._client.has_alive_target:
            return False
        tname = (self._client.target_name or '').lower()
        return bool(tname) and boss.lower() in tname

    def _find_boss(self, boss: str) -> bool:
        """Da TAB ate o alvo ser o boss. True se achou, False se nao apareceu."""
        for _ in range(10):
            if not self._client.running:
                return False
            self._client.new_target()      # TAB
            time.sleep(0.3)                # deixa o nome do alvo atualizar
            if self._target_is_boss(boss):
                return True
        return False

    def _run_boss(self, boss: str) -> bool:
        """Modo boss: garante que o alvo e o boss (TAB ate achar) e ataca SO ele."""
        if not self._target_is_boss(boss):
            if not self._find_boss(boss):
                self._client.set_action(f"🔍 Procurando boss: {boss}")
                return True   # boss nao apareceu -> espera (nao bate em mob comum)
        self._client.set_action(f"👑 BOSS: {boss}")
        self._command_pet()   # Tamer: manda o pet atacar o boss (1x por engajamento)
        while self._client.target_hp is not None and self._client.target_hp >= 0 and self._client.running:
            if not self._target_is_boss(boss):
                return True   # alvo deixou de ser o boss -> re-acha no proximo ciclo
            self._battle_pots()
            if not self._cur_attack_queue:
                self._cur_attack_queue = list(self.config.attacks)
            key, interval = self._cur_attack_queue.pop(0)
            self._client.press_key(key)
            time.sleep(int(interval) / 1000)
        return True

    def _command_pet(self) -> None:
        """Tamer: aperta a tecla de ataque do pet pra mandar o pet atacar o alvo atual.
        Chamado 1x ao engajar o alvo (o while segura o mob ate morrer) = 1 comando por mob."""
        if self._char_class != 'tamer':
            return
        key = (self.config.bindings or {}).get('pet_attack')
        if key:
            self._client.press_key(key)

    @staticmethod
    def _as_decimal(threshold) -> float:
        # UI accepts 0-100 (percent). If >1, treat as percent and convert.
        v = float(threshold)
        return v / 100 if v > 1 else v

    def _battle_pots(self):
        if self.config.bindings is None:
            return

        # MP pot -- so pota se passou a duracao do pot (16s); senao o anterior ainda
        # esta agindo (evita pot duplicado). Apos potar, espera ele agir.
        mp_key = self.config.bindings.get('battle_mana_pot')
        mp_thr = self.config.battle_mana_threshold
        if mp_key is not None and mp_thr is not None:
            if self._client.mana_percent < self._as_decimal(mp_thr) and self._use_pot(mp_key):
                self._wait_resource_refill("MP")

        # HP: a FAIRY se CURA (skill, em vez de pot -- ela nao usa pot de vida); DPS/Tamer
        # usam pot de HP (com cooldown de 16s). MP segue por pot pra todos (a cura gasta mana).
        hp_thr = self.config.battle_hp_threshold
        if hp_thr is not None and self._client.hp_percent < self._as_decimal(hp_thr):
            if self._char_class == 'fairy':
                heal_key = self.config.bindings.get('heal')
                if heal_key:
                    self._client.press_key(heal_key)   # cura nao e pot -> sem cooldown de pot
                    self._wait_resource_refill("HP")
            else:
                hp_key = self.config.bindings.get('battle_hp_pot')
                if hp_key and self._use_pot(hp_key):
                    self._wait_resource_refill("HP")

    def _wait_resource_refill(self, resource: str, full_pct: float = 0.95, timeout_s: int = POT_DURATION_SECS):
        """Apos usar pot, espera HP/MP encher antes de voltar a atacar.
        Atacar interrompe o regen do pot, entao precisa parar. O pot age ao longo de
        ~POT_DURATION_SECS (16s) -- por isso o timeout = duracao do pot (espera 'usar a
        pot toda', a nao ser que encha antes).
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
