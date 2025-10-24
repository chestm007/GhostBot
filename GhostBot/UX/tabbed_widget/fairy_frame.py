import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.TabFrame import TabFrame
from GhostBot.config import Config, FairyConfig
from GhostBot.lib.var_or_none import _float


class FairyFrame(TabFrame):
    def _init(self):
        self._vars = dict(
            heal_team=tk.StringVar(master=self, name="bot_config.fairy.heal_team", value=""),
            heal_self=tk.StringVar(master=self, name="bot_config.fairy.heal_self", value=""),
            heal=tk.StringVar(master=self, name="bot_config.fairy.heal", value=""),
            cure=tk.StringVar(master=self, name="bot_config.fairy.cure", value=""),
            revive=tk.StringVar(master=self, name="bot_config.fairy.revive", value=""),
        )

        ttk.Label(master=self, text="Heal Team At:", width=15).grid(row=0, column=0)
        ttk.Label(master=self, text="Heal Self At:", width=15).grid(row=1, column=0)
        ttk.Label(master=self, text="Heal Key:", width=15).grid(row=2, column=0)
        ttk.Label(master=self, text="Cure Key:", width=15).grid(row=3, column=0)
        ttk.Label(master=self, text="Revive Key:", width=15).grid(row=4, column=0)

        tk.Entry(master=self, textvariable=self._vars["heal_team"], takefocus=False).grid(row=0, column=1)
        tk.Entry(master=self, textvariable=self._vars["heal_self"], takefocus=False).grid(row=1, column=1)
        tk.Entry(master=self, textvariable=self._vars["heal"], takefocus=False).grid(row=2, column=1)
        tk.Entry(master=self, textvariable=self._vars["cure"], takefocus=False).grid(row=3, column=1)
        tk.Entry(master=self, textvariable=self._vars["revive"], takefocus=False).grid(row=4, column=1)

    def display_config(self, config: Config):
        if config.fairy:
            self.setvar('bot_config.fairy.heal_team', str(config.fairy.heal_team_threshold or ''))
            self.setvar('bot_config.fairy.heal_self', str(config.fairy.heal_self_threshold or ''))
            self.setvar('bot_config.fairy.heal', str((config.fairy.bindings or {}).get('heal', '')))
            self.setvar('bot_config.fairy.cure', str((config.fairy.bindings or {}).get('cure', '')))
            self.setvar('bot_config.fairy.revive', str((config.fairy.bindings or {}).get('revive', '')))
        else:
            self.clear()

    def extract_config(self) -> FairyConfig:
        _nullable_string = lambda x: x if x and x != 'None' else None
        bindings = dict(
            heal=_nullable_string(self.getvar('bot_config.fairy.heal')),
            cure=_nullable_string(self.getvar('bot_config.fairy.cure')),
            revive=_nullable_string(self.getvar('bot_config.fairy.revive')),
        )
        return FairyConfig(
            bindings=self._populate_bindings(bindings),
            heal_team_threshold=_float(self.getvar('bot_config.fairy.heal_team')),
            heal_self_threshold=_float(self.getvar('bot_config.fairy.heal_self')),
        )
