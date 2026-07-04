"""
Runner that monitors System chat and alerts drops on Discord (Sprint 4, Step 3).

Runs alongside the bot, even IN COMBAT (drops fall in combat). Every
_POLL_SECS reads the chat, accumulates drop counts on the client (for Dashboard) and
posts 'want' (🎯) and 'new' (❓) items to Discord. 'don't want' items are
ignored. Respects Stop: Runner only runs while bot is 'running'.
"""
from __future__ import annotations

import time

from GhostBot import drop_watcher as _dw
from GhostBot.discord_notify import send_drop_alert, send_death_alert, send_inventory_full_alert
from GhostBot.functions.runner import Runner, run_at_interval

_POLL_SECS = 2
_RELOAD_SECS = 20  # reload watchlist from time to time (edits apply without restart)


@run_at_interval(run_on_start=True, run_in_battle=True)
class DropWatch(Runner):
    """Reads chat every _POLL_SECS, counts drops and alerts on Discord."""

    def _setup(self):
        self._interval = _POLL_SECS
        self._disabled = not _dw.tesseract_available()
        if self._disabled:
            self._log_err("Tesseract not found -- drop detection off")
            return
        self._watcher = _dw.DropWatcher(_dw.default_watchlist_path())
        self._last_reload = time.time()
        self._box_was_full = False   # previous inventory state (only acts on transition)
        try:
            self._watcher.prime(self._client)
            self._box_was_full = self._watcher.box_full  # already full at Start -> do not re-dispatch
        except Exception as e:
            self._log_err("drop watch: prime failed: %s", e)

    def _run(self) -> bool:
        if self._disabled:
            return False
        if time.time() - self._last_reload > _RELOAD_SECS:
            self._watcher.reload_watchlist()
            self._last_reload = time.time()
        try:
            alerts, deltas = self._watcher.poll(self._client)
            for name, n in deltas.items():
                self._client.record_drop(name, n)   # count each drop (2 same = x2)
            for name, cat in alerts:
                if cat != "ignore":
                    send_drop_alert(name, cat, self._client.name)
                self._log_info("drop: %s [%s]", name, cat)
            self._check_inventory_full()
        except Exception as e:
            self._log_err("drop watch error: %s", e)
        return True

    def _check_inventory_full(self) -> None:
        """Acts ONLY on empty->full transition (no spam). Re-arms when the msg disappears.
        On full: alerts on Discord + sets sell_requested -> the sell in the main
        loop sells on the next turn (sequential with Attack; the sell timer
        remains as safety net if OCR does not catch it)."""
        if self._watcher.box_full:
            if not self._box_was_full:
                self._box_was_full = True
                self._log_info("INVENTORY FULL detected -> alert + request sell")
                try:
                    send_inventory_full_alert(self._client.name)
                except Exception as e:
                    self._log_err("inventory full alert failed: %s", e)
                self._client.sell_requested = True
        else:
            self._box_was_full = False


@run_at_interval(run_on_start=True, run_in_battle=True)
class DeathAlert(Runner):
    """Alerts on Discord when character dies (HP reaches 0).

    Does not depend on OCR/Tesseract. Only alerts on ALIVE->DEAD transition (no spam)
    and re-arms when HP returns above 0. Runs only with bot running (Stop stops it)."""

    def _setup(self):
        self._interval = 3
        self._was_alive = True

    def _run(self) -> bool:
        try:
            hp = self._client.hp
        except Exception:
            return False
        if hp is None:
            return False  # bad read / disconnected -> cannot confirm death
        if hp <= 0:
            if self._was_alive:
                self._was_alive = False
                send_death_alert(self._client.name)
                self._log_info("DEATH detected -> alert on Discord")
        else:
            self._was_alive = True
        return True
