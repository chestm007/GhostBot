import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.TabFrame import TabFrame
from GhostBot.config import Config, AttackConfig
from GhostBot.lib.var_or_none import _int, _float


class AttackFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            hp_low=self._create_entry("BattleHP Low:", 0, 0, ("bot_config.attack.battle_hp_low", str)),
            hp_key=self._create_entry("BattleHP Key:", 0, 2, ("bot_config.attack.battle_hp_key", str)),
            mp_low=self._create_entry("BattleMP Low:", 1, 0, ("bot_config.attack.battle_mp_low", str)),
            mp_key=self._create_entry("BattleMP Key:", 1, 2, ("bot_config.attack.battle_mp_key", str)),
            stuck=self._create_entry("Stuck Sec:", 2, 0, ("bot_config.attack.battle_stuck", str)),
            roam=self._create_entry("Roam Distance:", 3, 0, ("bot_config.attack.battle_roam", str))
        )

        ttk.Label(master=self, text="Attacks:", width=15).grid(row=4, column=0)
        self.attacks = tk.Text(master=self, width=11, height=5, takefocus=False)
        self.attacks.grid(row=4, column=1)

    def display_config(self, config: Config):
        if config.attack:
            hp_key = ''
            mp_key = ''
            if config.attack.bindings:
                hp_key = str(config.attack.bindings.get('battle_hp_pot', ''))
                mp_key = str(config.attack.bindings.get('battle_mana_pot', ''))
            self.setvar('bot_config.attack.battle_hp_key', hp_key)
            self.setvar('bot_config.attack.battle_mp_key', mp_key)

            self.setvar('bot_config.attack.battle_hp_low', str(config.attack.battle_hp_threshold or ''))
            self.setvar('bot_config.attack.battle_mp_low', str(config.attack.battle_mana_threshold or ''))
            self.setvar('bot.config.attack.battle_stuck', str(config.attack.stuck_interval or ''))
            self.setvar('bot_config.attack.battle_roam', str(config.attack.roam_distance or ''))
            self.attacks.delete(1.0, tk.END)
            self.attacks.insert(tk.END, "\n".join(f"{key} {delay}" for key, delay in config.attack.attacks))

        else:
            self.clear()

    def extract_config(self) -> AttackConfig:
        _san = lambda x: [x[0], int(x[1])]
        bindings = dict(
            battle_hp_pot=self._nullable_string(self.getvar('bot_config.attack.battle_hp_key')),
            battle_mana_pot=self._nullable_string(self.getvar('bot_config.attack.battle_mp_key')),
        )
        return AttackConfig(
            bindings=self._populate_bindings(bindings),
            attacks=[_san(v.split()) for v in self.attacks.get(1.0, tk.END).splitlines()] or None,
            stuck_interval=_int(self.getvar('bot_config.attack.battle_stuck')),
            battle_mana_threshold=_float(self.getvar('bot_config.attack.battle_mp_low')),
            battle_hp_threshold=_float(self.getvar('bot_config.attack.battle_hp_low')),
            roam_distance=_int(self.getvar('bot_config.attack.battle_roam')),
        )

    def _clear(self):
        self.attacks.delete(1.0, tk.END)
