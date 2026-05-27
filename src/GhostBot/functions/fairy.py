"""Fairy -- Modo Helper (cross-PC): segue e cura o 1o MEMBRO do grupo (o aliado).

Fluxo a cada ciclo (tudo BACKSTAGE -- NAO mexe o mouse real):
  - seleciona o aliado = clique no retrato do 1o membro do grupo (team_1);
  - cura o aliado -> ESPERA a conjuracao (gap, pra nao cortar o cast) -> P (segue);
  - buff periodico (no intervalo): combo no aliado -> gap -> P;
  - AUTO-CURA: se a vida da PROPRIA Fairy cair abaixo de heal_self_threshold
    (default 50%): F1 (auto-target) -> cura -> gap -> clica no 1o membro -> P.

Confirmado ao vivo (2026-05-26): F1 seleciona a propria Fairy; o left_click do
bot (SendMessage) seleciona o membro do grupo sem mexer o mouse. Coords dos
retratos em lib/talisman_ui_locations (team_1..team_4, ~81px de espacamento).
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

        # AUTO-CURA: se a vida DELA caiu, se cura primeiro.
        # Fluxo (pedido do dono): F1 -> cura -> aguarda conjuracao -> clica 1o membro -> P.
        # (o F1 tira a selecao do aliado, por isso re-seleciona o 1o membro no fim).
        if self._self_hp_low():
            self._client.set_action("💖 Auto-cura (HP baixo)")
            self._log_info('Helper: auto-cura (HP baixo) -> F1 + cura')
            self._client.press_key('f1')        # F1 = seleciona a propria Fairy
            time.sleep(0.3)
            if heal:
                self._client.press_key(heal)
            time.sleep(gap)                      # espera a conjuracao da cura
            self._select_ally()                  # volta a mirar o aliado (1o membro)
            self._client.press_key(follow)
            self._client.set_action("🏃 Seguindo aliado (P)")
            return True

        # Seleciona o aliado = 1o membro do grupo (clique backstage no retrato).
        # Garante a mira a cada ciclo (robusto, e recupera apos uma auto-cura).
        self._select_ally()

        # Buff periodico no aliado: combo -> folga (ultimo buff conjurar) -> P
        if self._should_buff():
            self._client.set_action("✨ Buffando aliado")
            self._log_info('Helper: buffando aliado...')
            for key, delay_ms in (self.config.buffs or []):
                if not self._client.running:
                    return True
                self._client.press_key(key)
                time.sleep(int(delay_ms) / 1000)
            time.sleep(gap)
            self._client.press_key(follow)
            self._client.set_action("🏃 Seguindo aliado (P)")
            self._last_buff_time = time.time()
            return True

        # Cura do aliado: aperta a cura -> ESPERA a conjuracao (gap) -> P (sem cortar o cast).
        self._client.set_action("💚 Curando aliado")
        if heal:
            self._client.press_key(heal)
        time.sleep(gap)
        self._client.press_key(follow)
        self._client.set_action("🏃 Seguindo aliado (P)")
        return True

    def _select_ally(self) -> None:
        """Seleciona o aliado = 1o membro do grupo, clicando no retrato (team_1).
        BACKSTAGE (SendMessage via left_click, NAO mexe o mouse real). Confirmado ao
        vivo que o left_click do bot seleciona o membro do grupo."""
        self._client.left_click(UI_locations.team_1)
        time.sleep(0.2)

    def _self_hp_low(self) -> bool:
        """True se a vida da PROPRIA Fairy caiu abaixo do limite de auto-cura
        (FairyConfig.heal_self_threshold; default 50%). Aceita 0-1 ou 0-100."""
        thr = self.config.heal_self_threshold
        thr = float(thr) if thr is not None else 0.5
        if thr > 1:            # UI as vezes manda 0-100 em vez de 0.0-1.0
            thr = thr / 100
        try:
            return self._client.hp_percent < thr
        except Exception:
            return False

    def _should_buff(self) -> bool:
        """True se ha buffs configurados E ja passou o intervalo desde o ultimo buff."""
        if not self.config.buffs or not self.config.buff_interval_mins:
            return False
        interval_s = int(self.config.buff_interval_mins) * 60
        return (time.time() - self._last_buff_time) >= interval_s
