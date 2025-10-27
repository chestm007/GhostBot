import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.TabFrame import TabFrame
from GhostBot.config import Config, AttackConfig
from GhostBot.lib.var_or_none import _int, _float


class AttackFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            hp_low=tk.StringVar(master=self, name="bot_config.attack.battle_hp_low", value=""),
            hp_key=tk.StringVar(master=self, name="bot_config.attack.battle_hp_key", value=""),
            mp_low=tk.StringVar(master=self, name="bot_config.attack.battle_mp_low", value=""),
            mp_key=tk.StringVar(master=self, name="bot_config.attack.battle_mp_key", value=""),
            stuck=tk.StringVar(master=self, name="bot_config.attack.battle_stuck", value=""),
            roam=tk.StringVar(master=self, name="bot_config.attack.battle_roam", value="")
        )

        ttk.Label(master=self, text="BattleHP Low:", width=15).grid(row=0, column=0)
        ttk.Label(master=self, text="BattleHP Key:", width=15).grid(row=0, column=2)
        ttk.Label(master=self, text="BattleMP Low:", width=15).grid(row=1, column=0)
        ttk.Label(master=self, text="BattleMP Key:", width=15).grid(row=1, column=2)
        ttk.Label(master=self, text="Stuck Sec:", width=15).grid(row=2, column=0)
        ttk.Label(master=self, text="Roam Distance:", width=15).grid(row=3, column=0)

        tk.Entry(master=self, width=15, textvariable=self._vars['hp_low'], takefocus=False).grid(row=0, column=1)
        tk.Entry(master=self, width=15, textvariable=self._vars['hp_key'], takefocus=False).grid(row=0, column=3)
        tk.Entry(master=self, width=15, textvariable=self._vars['mp_low'], takefocus=False).grid(row=1, column=1)
        tk.Entry(master=self, width=15, textvariable=self._vars['mp_key'], takefocus=False).grid(row=1, column=3)
        tk.Entry(master=self, width=15, textvariable=self._vars['stuck'], takefocus=False).grid(row=2, column=1)
        tk.Entry(master=self, width=15, textvariable=self._vars['roam'], takefocus=False).grid(row=3, column=1)

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
        _nullable_string = lambda x: x if x and x != 'None' else None
        bindings = dict(
            battle_hp_pot=_nullable_string(self.getvar('bot_config.attack.battle_hp_key')),
            battle_mana_pot=_nullable_string(self.getvar('bot_config.attack.battle_mp_key')),
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
