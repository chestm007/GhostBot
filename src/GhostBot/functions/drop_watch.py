"""
Runner que monitora o chat System e avisa drops no Discord (Sprint 4, Etapa 3).

Roda junto com o bot, inclusive EM COMBATE (drops caem em combate). A cada
_POLL_SECS le o chat, acumula a contagem de drops no cliente (pro Dashboard) e
posta no Discord os itens 'quero' (🎯) e 'novos' (❓). Itens 'nao quero' sao
ignorados. Respeita o Stop: o Runner so roda enquanto o bot esta 'running'.
"""
from __future__ import annotations

import time

from GhostBot import drop_watcher as _dw
from GhostBot.discord_notify import send_drop_alert, send_death_alert
from GhostBot.functions.runner import Runner, run_at_interval

_POLL_SECS = 2
_RELOAD_SECS = 20  # recarrega a watchlist de tempos em tempos (edicoes valem sem reiniciar)


@run_at_interval(run_on_start=True, run_in_battle=True)
class DropWatch(Runner):
    """Le o chat a cada _POLL_SECS, conta os drops e alerta no Discord."""

    def _setup(self):
        self._interval = _POLL_SECS
        self._disabled = not _dw.tesseract_available()
        if self._disabled:
            self._log_err("Tesseract nao encontrado -- deteccao de drop desligada")
            return
        self._watcher = _dw.DropWatcher(_dw.default_watchlist_path())
        self._last_reload = time.time()
        try:
            self._watcher.prime(self._client)
        except Exception as e:
            self._log_err("drop watch: prime falhou: %s", e)

    def _run(self) -> bool:
        if self._disabled:
            return False
        if time.time() - self._last_reload > _RELOAD_SECS:
            self._watcher.reload_watchlist()
            self._last_reload = time.time()
        try:
            alerts, deltas = self._watcher.poll(self._client)
            for name, n in deltas.items():
                self._client.record_drop(name, n)   # conta cada drop (2 iguais = x2)
            for name, cat in alerts:
                if cat != "ignore":
                    send_drop_alert(name, cat, self._client.name)
                self._log_info("drop: %s [%s]", name, cat)
        except Exception as e:
            self._log_err("drop watch erro: %s", e)
        return True


@run_at_interval(run_on_start=True, run_in_battle=True)
class DeathAlert(Runner):
    """Avisa no Discord quando o personagem morre (HP chega a 0).

    Nao depende de OCR/Tesseract. So alerta na TRANSICAO vivo->morto (nao spamma)
    e re-arma quando o HP volta acima de 0. Roda so com o bot rodando (Stop para)."""

    def _setup(self):
        self._interval = 3
        self._was_alive = True

    def _run(self) -> bool:
        try:
            hp = self._client.hp
        except Exception:
            return False
        if hp is None:
            return False  # leitura ruim / desconectado -> nao conclui morte
        if hp <= 0:
            if self._was_alive:
                self._was_alive = False
                send_death_alert(self._client.name)
                self._log_info("MORTE detectada -> alerta no Discord")
        else:
            self._was_alive = True
        return True
