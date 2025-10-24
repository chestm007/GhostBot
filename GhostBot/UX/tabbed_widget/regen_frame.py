import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.TabFrame import TabFrame
from GhostBot.bot_controller import ExtendedClient
from GhostBot.config import Config, RegenConfig
from GhostBot.lib.var_or_none import _float, _tuple


class RegenFrame(TabFrame):
    def _init(self, client: ExtendedClient):
        self.client = client

        self._vars = dict(
            hp_low=tk.StringVar(master=self, name="bot_config.regen.hp_low", value=""),
            hp_key=tk.StringVar(master=self, name="bot_config.regen.hp_key", value=""),
            mp_low=tk.StringVar(master=self, name="bot_config.regen.mp_low", value=""),
            mp_key=tk.StringVar(master=self, name="bot_config.regen.mp_key", value=""),
            sit_key=tk.StringVar(master=self, name="bot_config.regen.sit_key", value=""),
            spot=tk.StringVar(master=self, name="bot_config.regen.spot", value=""),
        )

        ttk.Label(master=self, text="HP Low:", width=15).grid(row=0, column=0)
        ttk.Label(master=self, text="HP Key:", width=15).grid(row=0, column=2)
        ttk.Label(master=self, text="MP Low:", width=15).grid(row=1, column=0)
        ttk.Label(master=self, text="MP Key:", width=15).grid(row=1, column=2)
        ttk.Label(master=self, text="Sit Key:", width=15).grid(row=2, column=0)
        ttk.Label(master=self, text="Spot:", width=15).grid(row=3, column=0)

        tk.Entry(master=self, width=15, textvariable=self._vars['hp_low'], takefocus=False).grid(row=0, column=1)
        tk.Entry(master=self, width=15, textvariable=self._vars['hp_key'], takefocus=False).grid(row=0, column=3)
        tk.Entry(master=self, width=15, textvariable=self._vars['mp_low'], takefocus=False).grid(row=1, column=1)
        tk.Entry(master=self, width=15, textvariable=self._vars['mp_key'], takefocus=False).grid(row=1, column=3)
        tk.Entry(master=self, width=15, textvariable=self._vars['sit_key'], takefocus=False).grid(row=2, column=1)
        tk.Entry(master=self, width=15, textvariable=self._vars['spot'], takefocus=False).grid(row=3, column=1)

        ttk.Button(
            master=self, text="Current", command=lambda: self._set_spot_as_current()
        ).grid(row=3, column=2)

    def _set_spot_as_current(self):
        self._vars['spot'].set(eval(self.master.getvar('char_info.position')))
        print(self.extract_config())

    def display_config(self, config: Config):
        def _format_spot(_spot):
            if _spot:
                return f"{' '.join(map(str, _spot))}"
            return ''

        if config.attack:
            self.setvar('bot_config.regen.hp_low', str(config.regen.hp_threshold or ''))
            self.setvar('bot_config.regen.hp_key', str((config.regen.bindings or {}).get('hp_pot')) or '')
            self.setvar('bot_config.regen.mp_low', str(config.regen.mana_threshold or ''))
            self.setvar('bot_config.regen.mp_key', str((config.regen.bindings or {}).get('mana_pot')) or '')
            self.setvar('bot_config.regen.sit_key', str((config.regen.bindings or {}).get('sit')) or '')
            self.setvar('bot_config.regen.spot', _format_spot(config.regen.spot))

        else:
            self.clear()

    def extract_config(self) -> RegenConfig:
        _nullable_string = lambda x: x if x and x != 'None' else None
        bindings = dict(
            hp_pot=_nullable_string(self.getvar('bot_config.regen.hp_key')),
            mana_pot=_nullable_string(self.getvar('bot_config.regen.mp_key')),
            sit=_nullable_string(self.getvar('bot_config.regen.sit_key')),
        )
        return RegenConfig(
            bindings=self._populate_bindings(bindings),
            hp_threshold=_float(self.getvar('bot_config.regen.hp_low')),
            mana_threshold=_float(self.getvar('bot_config.regen.mp_low')),
            spot=_tuple(self.getvar('bot_config.regen.spot')),
        )
