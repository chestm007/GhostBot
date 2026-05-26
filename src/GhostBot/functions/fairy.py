"""Fairy -- Modo Helper (cross-PC): segue e cura UM aliado SO por TECLA.

Reescrita limpa (2026-05-26). NAO clica em retrato, NAO le HP do aliado, NAO
detecta time -- nada disso (era o que bugava e nao servia cross-PC).

Fluxo: o usuario deixa o ALIADO selecionado no jogo e da Start na Fairy. A cada
ciclo a Fairy aperta a tecla de cura, ESPERA a conjuracao (a folga, pra nao
cortar o cast de ~2s), e aperta o P (que segue o alvo selecionado). No intervalo
de buff: aplica o combo -> folga -> P. Sempre termina com P pra manter o follow.

TODO (proxima etapa): autocura -- se o HP da PROPRIA Fairy cair abaixo de ~50%,
ela se cura (vai usar a tecla CERTA de auto-target que o dono conhece).
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from GhostBot.functions.runner import Runner

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow
    from GhostBot.config import FairyConfig


class Fairy(Runner):
    def __init__(self, bot_controller, client: "BotClientWindow"):
        super().__init__(client)
        self.config: FairyConfig = client.config.fairy
        self._bot_controller = bot_controller
        self._last_buff_time = 0  # timestamp do ultimo ciclo de buff (0 = nunca)

    def _run(self) -> bool:
        if not self.config.helper_mode:
            self._client.set_action("🧚 Fairy ociosa (ligue o Modo Helper)")
            return True
        return self._run_helper()

    def _run_helper(self) -> bool:
        follow = (self.config.bindings or {}).get('follow') or 'p'
        heal = (self.config.bindings or {}).get('heal')
        gap = float(self.config.heal_interval_secs or 3)  # conjuracao + folga antes do P
        alvo = self._client.target_name or 'aliado'

        # Buff periodico: combo -> folga (ultimo buff conjurar) -> P
        if self._should_buff():
            self._client.set_action(f"✨ Buffando {alvo}")
            self._log_info(f'Helper: buffando {alvo}...')
            for key, delay_ms in (self.config.buffs or []):
                if not self._client.running:
                    return True
                self._client.press_key(key)
                time.sleep(int(delay_ms) / 1000)
            time.sleep(gap)
            self._client.press_key(follow)
            self._client.set_action(f"🏃 Seguindo {alvo} (P)")
            self._last_buff_time = time.time()
            return True

        # Cura: aperta a cura -> ESPERA a conjuracao (gap) -> P (sem cortar o cast).
        self._client.set_action(f"💚 Curando {alvo}")
        if heal:
            self._client.press_key(heal)
        time.sleep(gap)
        self._client.press_key(follow)
        self._client.set_action(f"🏃 Seguindo {alvo} (P)")
        return True

    def _should_buff(self) -> bool:
        """True se ha buffs configurados E ja passou o intervalo desde o ultimo buff."""
        if not self.config.buffs or not self.config.buff_interval_mins:
            return False
        interval_s = int(self.config.buff_interval_mins) * 60
        return (time.time() - self._last_buff_time) >= interval_s
