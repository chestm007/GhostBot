"""Modo Cave Boss -- papel por char (Tank / DPS / Fairy).

A aba "Boss" da UI escolhe o papel; este runner age conforme `config.boss.role`.
Os 3 papeis estao implementados (2026-05-27):

- TANK: trava no boss (TAB ate o nome), ataca com o combo SEM parar, e a cada
  `buff_interval_secs` reaplica os buffs do tank (so aperta a tecla; auto-cast, nao
  troca de alvo). Pots HP/MP opcionais (tecla vazia = off; tank deixa MP vazio).
- DPS: bate no boss; se PUXA AGGRO (perde vida em combate -- inferimos, nao da pra ler
  o aggro do boss direto) recua com F1 -> espera sair de combate -> o tank repuxa ->
  volta. MP baixo: F1 -> espera sair de combate -> pot. Aggro sempre ligado.
- FAIRY: spama a tecla de cura no ALVO ATUAL a cada `heal_interval_secs`; o jogador
  troca o alvo (sem mira automatica -- nao da pra ler o HP dos outros membros).

Reusa a mesma logica de boss-lock do Attack (_target_is_boss / _find_boss).
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from GhostBot.functions.runner import Runner, POT_DURATION_SECS

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
            return self._run_dps()
        if role == 'fairy':
            return self._run_fairy()
        self._client.set_action("🐉 Boss: selecione um Papel na aba")
        return True

    # ------------------------------------------------------------------- DPS
    def _run_dps(self) -> bool:
        """Bate no boss; se PUXAR AGGRO (perde vida em combate) recua: F1 -> espera sair de
        combate -> o tank repuxa -> volta. Mesma logica pra MP baixo: F1 -> espera sair de
        combate -> pot. (Nao da pra ler o aggro do boss direto; inferimos pela queda de HP.)"""
        boss = (self.config.boss_name or '').strip()
        if not boss:
            self._client.set_action("🐉 DPS: configure o Nome do Boss")
            return True

        # MP baixo (antes de engajar) -> recua e recupera
        if self._mp_low():
            return self._recover_mp(boss)

        if not self._target_is_boss(boss):
            if not self._find_boss(boss):
                self._client.set_action(f"🔍 Procurando boss: {boss}")
                return True

        self._client.set_action(f"⚔️ DPS no boss: {boss}")
        last_hp = self._safe_hp()
        while self._client.target_hp is not None and self._client.target_hp >= 0 and self._client.running:
            if not self._target_is_boss(boss):
                return True
            # AGGRO: perdi vida em combate -> puxei o aggro -> recua (F1) e espera o tank
            cur_hp = self._safe_hp()
            if last_hp is not None and cur_hp is not None and cur_hp < last_hp:
                return self._backoff_aggro(boss)
            last_hp = cur_hp
            # MP baixo no meio da luta -> recua e recupera
            if self._mp_low():
                return self._recover_mp(boss)
            self._hp_pot_simple()   # pot HP opcional (tecla vazia = off)
            if not self._cur_attack_queue:
                self._cur_attack_queue = list(self.config.attacks or [])
            if not self._cur_attack_queue:
                self._client.set_action("⚔️ DPS: configure o Combo de ataque")
                return True
            key, interval = self._cur_attack_queue.pop(0)
            self._client.press_key(key)
            time.sleep(int(interval) / 1000)
        return True

    def _backoff_aggro(self, boss: str) -> bool:
        """Puxou aggro: F1 (seleciona a si mesmo -> para de atacar o boss) -> espera sair de
        combate (o tank repuxa pela ameaca) -> TAB pra re-pegar o boss -> volta a bater."""
        self._client.set_action("🛑 Puxei aggro → F1, esperando o tank repuxar")
        self._log_info("DPS: puxei aggro -> F1 + espera sair de combate")
        self._client.press_key('f1')
        self._wait_out_of_combat()
        self._find_boss(boss)   # TAB de volta pro boss -> continua no proximo ciclo
        return True

    def _recover_mp(self, boss: str) -> bool:
        """MP baixo: F1 (para de atacar) -> espera sair de combate -> toma o pot MP -> deixa
        subir um pouco -> TAB pra RE-PEGAR o alvo (pedido do dono) -> volta a bater. Sem pot
        configurado, so recua, espera e re-pega."""
        self._client.set_action("💧 MP baixo → F1, recuperando fora de combate")
        self._log_info("DPS: MP baixo -> F1 + recupera")
        self._client.press_key('f1')
        self._wait_out_of_combat()
        mp_key = (self.config.bindings or {}).get('battle_mana_pot')
        if mp_key:
            self._use_pot(mp_key)   # so pota se fora do cooldown (16s) -- evita pot duplicado
            thr = self._as_decimal(self.config.battle_mana_threshold) if self.config.battle_mana_threshold is not None else 0.5
            # espera o MP subir (recuou, nao esta atacando -> o pot age). Ate a duracao do pot.
            start = time.time()
            while self._client.running and (time.time() - start) < POT_DURATION_SECS:
                time.sleep(0.5)
                try:
                    if self._client.mana_percent >= thr:
                        break
                except Exception:
                    break
        self._find_boss(boss)   # TAB de volta pro alvo -> continua batendo
        return True

    def _wait_out_of_combat(self, timeout_s: int = 20) -> None:
        """Espera o personagem SAIR de combate (o tank repuxou). Bounded por timeout e
        respeita o Stop (client.running)."""
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
        """Pot HP em combate (opcional, em branco = off). HP only -- o MP do DPS usa o recuo.
        Com cooldown (16s) pra nao re-potar enquanto o pot anterior ainda age."""
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
        """Cura no ALVO ATUAL (opcao 'a'): a Fairy so spama a tecla de cura; o jogador
        troca o alvo (clica em quem precisa). Sem logica de mira -- nao da pra ler o HP
        dos outros membros. Pots HP/MP proprios sao opcionais (tecla vazia = off)."""
        heal = (self.config.bindings or {}).get('heal')
        if not heal:
            self._client.set_action("🧚 Fairy: configure a Tecla de Cura")
            return True
        self._battle_pots()   # cuida da PROPRIA Fairy (HP/MP), se configurado
        self._client.set_action("💚 Curando (alvo atual)")
        self._client.press_key(heal)
        time.sleep(float(self.config.heal_interval_secs or 2))
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
            # TANK NAO pota no boss -- as Fairies curam o tank (decisao do dono).
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
        """Pots HP/MP PROPRIOS, com cooldown (16s) pra nao re-potar. Usado pela FAIRY
        (pots dela mesma). O TANK NAO chama isto -- as Fairies curam o tank no boss.
        Opcionais: tecla em branco = desligado."""
        b = self.config.bindings or {}

        mp_key = b.get('battle_mana_pot')
        mp_thr = self.config.battle_mana_threshold
        if mp_key and mp_thr is not None and self._client.mana_percent < self._as_decimal(mp_thr):
            self._use_pot(mp_key)

        hp_key = b.get('battle_hp_pot')
        hp_thr = self.config.battle_hp_threshold
        if hp_key and hp_thr is not None and self._client.hp_percent < self._as_decimal(hp_thr):
            self._use_pot(hp_key)
