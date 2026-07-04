import tkinter as tk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import create_entry, create_int_slider, ComboWidget
from GhostBot.config import Config, FairyConfig
from GhostBot.lib.var_or_none import var_or_none


class FairyFrame(TabFrame):
    """Fairy tab -- Helper Mode (follows + heals an ally per key, cross-PC)."""

    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            helper_mode=create_entry(
                self, "Helper Mode:", 0, 0, ("bot_config.fairy.helper_mode", bool),
                hint="Turns on Helper mode: the Fairy follows (key P) and always heals one ally, "
                     "just by key. Select the ally in the game, the Fairy in the list, and press Start.",
            ),
            heal=create_entry(
                self, "Heal Key:", 1, 0, ("bot_config.fairy.heal", str), entry_width=3,
                hint="Heal skill key.",
            ),
            follow=create_entry(
                self, "Follow Key:", 1, 4, ("bot_config.fairy.follow", str), entry_width=3,
                hint="Key that follows the selected target (default P).",
            ),
            heal_interval=create_int_slider(
                self, "Cast time (s):", 2, 0, "bot_config.fairy.heal_interval",
                default=3, min_val=1, max_val=15, suffix="s",
                hint="Heal cast time + pause, BEFORE pressing P (and how often "
                     "it heals). The heal takes ~2s; the default 3s gives 1s of pause so it doesn't "
                     "interrupt the cast. Change here if the game changes cast time.",
            ),
            buff_interval=create_int_slider(
                self, "Buff every:", 3, 0, "bot_config.fairy.buff_interval",
                default=15, min_val=1, max_val=60, suffix="min",
                hint="Frequency of re-buffing the ally (in minutes). Buffs last 10-20 min.",
            ),
        )

        # Buff combo (no TAB button -- buff doesn't switch target)
        self._buff_combo = ComboWidget(
            self, "Buffs:", grid_row=4, grid_column=0,
            hint="Sequence of buffs applied to the ally. Each row: key + interval ms. "
                 "After the combo, the Fairy presses P again to follow.",
            show_tab_button=False,
        )
        self._buff_combo.add_row()

    def display_config(self, config: Config):
        if config.fairy:
            self.setvar('bot_config.fairy.helper_mode', bool(config.fairy.helper_mode))
            self.setvar('bot_config.fairy.heal', str((config.fairy.bindings or {}).get('heal', '')))
            self.setvar('bot_config.fairy.follow', str((config.fairy.bindings or {}).get('follow', '')))
            self.setvar('bot_config.fairy.heal_interval', str(config.fairy.heal_interval_secs or '3'))
            self.setvar('bot_config.fairy.buff_interval', str(config.fairy.buff_interval_mins or ''))
            self._buff_combo.set_attacks(config.fairy.buffs or [])
        else:
            self.clear()

    def extract_config(self) -> FairyConfig:
        bindings = dict(
            heal=self._nullable_string(self.getvar('bot_config.fairy.heal')),
            follow=self._nullable_string(self.getvar('bot_config.fairy.follow')),
        )
        return FairyConfig(
            bindings=self._populate_bindings(bindings),
            helper_mode=var_or_none(self.getvar('bot_config.fairy.helper_mode')),
            heal_interval_secs=var_or_none(self.getvar('bot_config.fairy.heal_interval'), float),
            buff_interval_mins=var_or_none(self.getvar('bot_config.fairy.buff_interval')),
            buffs=self._buff_combo.get_attacks() or None,
        )

    def _clear(self):
        self._buff_combo.set_attacks([])
