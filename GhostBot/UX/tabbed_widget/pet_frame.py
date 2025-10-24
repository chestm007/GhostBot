import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.TabFrame import TabFrame
from GhostBot.config import Config, PetConfig
from GhostBot.lib.var_or_none import _int


class PetFrame(TabFrame):
    def _init(self):
        self._vars = dict(
            spawn_interval=tk.StringVar(master=self, name="bot_config.pet.spawn_interval", value=""),
            spawn_key=tk.StringVar(master=self, name="bot_config.pet.spawn_key", value=""),
            food_interval=tk.StringVar(master=self, name="bot_config.pet.food_interval", value=""),
            food_key=tk.StringVar(master=self, name="bot_config.pet.food_key", value=""),
        )
        ttk.Label(master=self, text="Spawn Interval:", width=15).grid(row=0, column=0)
        ttk.Label(master=self, text="Spawn Key:", width=15).grid(row=0, column=2)
        ttk.Label(master=self, text="Feed Interval:", width=15).grid(row=1, column=0)
        ttk.Label(master=self, text="Feed Key:", width=15).grid(row=1, column=2)

        tk.Entry(master=self, width=15, textvariable=self._vars['spawn_interval'], takefocus=False).grid(row=0, column=1)
        tk.Entry(master=self, width=15, textvariable=self._vars['spawn_key'], takefocus=False).grid(row=0, column=3)
        tk.Entry(master=self, width=15, textvariable=self._vars['food_interval'], takefocus=False).grid(row=1, column=1)
        tk.Entry(master=self, width=15, textvariable=self._vars['food_key'], takefocus=False).grid(row=1, column=3)

    def display_config(self, config: Config):
        if config.pet:
            self.setvar('bot_config.pet.spawn_interval', str(config.pet.spawn_interval_mins or ''))
            self.setvar('bot_config.pet.spawn_key', str((config.pet.bindings or {}).get('spawn', '')))
            self.setvar('bot_config.pet.food_interval', str(config.pet.food_interval_mins or ''))
            self.setvar('bot_config.pet.food_key', str((config.pet.bindings or {}).get('food', '')))
        else:
            self.clear()

    def extract_config(self) -> PetConfig:
        _nullable_string = lambda x: x if x and x != 'None' else None
        bindings = dict(
            spawn=_nullable_string(self.getvar('bot_config.pet.spawn_key')),
            food=_nullable_string(self.getvar('bot_config.pet.food_key')),
        )
        return PetConfig(
            bindings=self._populate_bindings(bindings),
            spawn_interval_mins=_int(self.getvar('bot_config.pet.spawn_interval')),
            food_interval_mins=_int(self.getvar('bot_config.pet.food_interval')),
        )
