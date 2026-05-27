"""Modo Cave Boss -- papel por char (Tank / DPS / Fairy).

A aba "Boss" da UI escolhe o papel; este runner age conforme `config.boss.role`.

Passo 1 (2026-05-27): TANK funcional -- trava no boss (TAB ate o nome), ataca com o
combo SEM parar, e a cada `buff_interval_secs` reaplica os buffs do tank (so aperta a
tecla; buff de tank e auto-cast, nao troca de alvo). Pots HP/MP opcionais (tecla em
branco = desligado -- o tank normalmente nao usa MP). DPS e Fairy ficam como placeholder
(em construcao) ate os proximos passos.

Reusa a mesma logica de boss-lock do Attack (_target_is_boss / _find_boss).
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from GhostBot.functions.runner import Runner

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow
    from GhostBot.config import BossConfig


class Boss(Runner):
    def __init__(self, client: "BotClientWindow"):
        super().__init__(client)
        self.config: BossConfig = client.config.boss
        self._cur_attack_queue: list = []
        self._last_buff_time = 0.0   # timestamp do ultimo ciclo de buffs do tank

    def _run(self) -> bool:
        role = (self.config.role or '').strip().lower()
        if role == 'tank':
            return self._run_tank()
        if role == 'dps':
            self._client.set_action("⚔️ DPS no boss (em construção)")
            return True
        if role == 'fairy':
            self._client.set_action("🧚 Fairy no boss (em construção)")
            return True
        self._client.set_action("🐉 Boss: selecione um Papel na aba")
        return True

    # ------------------------------------------------------------------ TANK
    def _run_tank(self) -> bool:
        boss = (self.config.boss_name or '').strip()
        if not boss:
            self._client.set_action("🐉 Tank: configure o Nome do Boss")
            return True

        # garante que o alvo e o boss (TAB ate achar)
        if not self._target_is_boss(boss):
            if not self._find_boss(boss):
                self._client.set_action(f"🔍 Procurando boss: {boss}")
                return True

        self._client.set_action(f"🛡️ TANK no boss: {boss}")
        while self._client.target_hp is not None and self._client.target_hp >= 0 and self._client.running:
            if not self._target_is_boss(boss):
                return True   # alvo deixou de ser o boss -> re-acha no proximo ciclo
            self._maybe_buff()
            self._battle_pots()
            if not self._cur_attack_queue:
                self._cur_attack_queue = list(self.config.attacks or [])
            if not self._cur_attack_queue:
                self._client.set_action(f"🛡️ Tank: configure o Combo de ataque")
                return True   # sem combo -> nada a apertar
            key, interval = self._cur_attack_queue.pop(0)
            self._client.press_key(key)
            time.sleep(int(interval) / 1000)
        return True

    def _maybe_buff(self) -> None:
        """Reaplica os buffs do tank a cada buff_interval_secs (so aperta a tecla --
        buff de tank e auto-cast, nao troca de alvo)."""
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

    # ------------------------------------------------- boss targeting (= Attack)
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

    # ------------------------------------------------------------- pots (opcionais)
    @staticmethod
    def _as_decimal(threshold) -> float:
        v = float(threshold)
        return v / 100 if v > 1 else v

    def _battle_pots(self) -> None:
        """Pots HP/MP em combate. Opcionais: tecla em branco = desligado (o tank
        normalmente deixa o MP vazio). Nao espera recuperar (tank nao pode soltar o boss)."""
        b = self.config.bindings or {}

        mp_key = b.get('battle_mana_pot')
        mp_thr = self.config.battle_mana_threshold
        if mp_key and mp_thr is not None and self._client.mana_percent < self._as_decimal(mp_thr):
            self._client.press_key(mp_key)

        hp_key = b.get('battle_hp_pot')
        hp_thr = self.config.battle_hp_threshold
        if hp_key and hp_thr is not None and self._client.hp_percent < self._as_decimal(hp_thr):
            self._client.press_key(hp_key)
