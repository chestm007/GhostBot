from __future__ import annotations

import time
from typing import TYPE_CHECKING

from GhostBot.functions.runner import Locational
from GhostBot.lib.math import seconds

if TYPE_CHECKING:
    from GhostBot.config import RegenConfig
    from GhostBot.controller.bot_controller import BotClientWindow


class Regen(Locational):
    MAX_REGEN_SECS = 16  # rede de seguranca: nunca descansa mais que isso -> volta a atacar

    def __init__(self, client: BotClientWindow, fairy_activated: bool = False):
        super().__init__(client=client)

        self._fairy_activated = fairy_activated
        self.config: RegenConfig = self._client.config.regen
        self._mana_threshold = self._normalize_threshold(self.config.mana_threshold, default=0.75)
        self._hp_threshold = self._normalize_threshold(self.config.hp_threshold, default=0.75)
        # classes sem mana (ex: Assassin) ignoram o MP no descanso
        self._ignore_mana = bool(getattr(self.config, 'ignore_mana', False))
        # Recupera ate ~CHEIO antes de voltar a atacar (nao desperdica pot levantando
        # a 85%). O timeout MAX_REGEN_SECS (60s) impede sentar pra sempre se nao encher.
        self._hp_recovered = 0.95
        self._mana_recovered = 0.95

    @staticmethod
    def _normalize_threshold(value, default: float) -> float:
        v = float(value if value is not None else default)
        # UI accepts 0-100 (percent). If user entered >1, treat as percent and convert.
        return v / 100 if v > 1 else v

    def _run(self) -> bool:
        """:return: True se descansou/voltou ok; False se foi atacado ou segue em combate.

        Ordem (pedido do dono): 1) NUNCA descansa/volta ao spot em COMBATE -> espera
        sair; 2) RECUPERA primeiro (pot + sentar NO LUGAR ATUAL); 3) so DEPOIS de
        recuperado, e fora de combate, volta pro spot."""
        if not (self._mana_low() or self._hp_low()):
            return False

        self._client.set_action("🪑 Descansando (HP/MP)")

        # 1) Em combate? Espera sair. Se nao sair, deixa o Attack/battle_pots cuidar
        # e tenta de novo no proximo ciclo (NAO senta nem volta ao spot em combate).
        if self._client.in_battle:
            start_wait = time.time()
            while self._client.in_battle and time.time() - start_wait < seconds(seconds=3):
                time.sleep(0.5)
            if self._client.in_battle:
                return False

        self._log_info('low hp/mana, starting Regen')

        # 2) RECUPERA PRIMEIRO -- pot + sentar ONDE ESTA (ainda nao vai pro spot)
        if self.config.bindings:
            self._use_hp_pot()
            self._use_mana_pot()
        hp = int(self._client.hp)
        regen_start = time.time()
        while not self._recovered() and self._client.running:
            # PRIORIDADE ATAQUE: se entrou em combate (mob agressivo chegou perto) ou
            # esta apanhando, PARA de descansar e volta a atacar na hora.
            if self._client.in_battle or int(self._client.hp) < hp:
                self._log_debug('Ouch -> volta a atacar')
                return False
            if time.time() - regen_start > self.MAX_REGEN_SECS:
                self._log_info('Regen atingiu o limite (%ss), seguindo', self.MAX_REGEN_SECS)
                break
            self._sit()  # senta ONDE ESTA (nao vai pro spot)
            hp = int(self._client.hp)
            # descansa em passos curtos checando combate -> resposta rapida a mob agressivo
            for _ in range(3):
                time.sleep(0.5)
                if self._client.in_battle:
                    self._log_debug('Mob agressivo no descanso -> volta a atacar')
                    return False

        # 3) RECUPERADO -> levanta e SO ENTAO volta pro spot (so fora de combate)
        self._stand()
        if not self._client.in_battle:
            self._client.set_action("🏃 Voltando ao spot")
            self._goto_start_location()
        return True

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
        # pot funciona EM PE e ONDE ESTA (nao vai pro spot) -- recupera primeiro.
        # _use_pot tem cooldown (16s) pra nao re-potar antes do pot anterior agir.
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
        """Levanta (se sentado) antes de voltar a andar/atacar. sit() faz toggle."""
        if self._client.sitting:
            self._log_debug('standing up')
            self._client.sit(self.config.bindings.get('sit'))
