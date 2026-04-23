import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.config import Config, BuffConfig
from GhostBot.lib.var_or_none import var_or_none
from UX.utils import create_entry


class BuffFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            interval=create_entry(self, "Interval:", 0, 0, ("bot_config.buff.interval", str)),
        )

        ttk.Label(master=self, text="Buffs:", width=15).grid(row=4, column=0)
        self.buffs = tk.Text(master=self, width=11, height=5, takefocus=False)
        self.buffs.grid(row=4, column=1)

    def display_config(self, config: Config):
        if config.buff:
            self.setvar('bot_config.buff.interval', str(config.buff.interval or ''))
            self.buffs.delete(1.0, tk.END)
            self.buffs.insert(tk.END, "\n".join(f"{key} {delay}" for key, delay in config.buff.buffs))
        else:
            self.clear()

    def extract_config(self) -> BuffConfig:
        _san = lambda x: [x[0], int(x[1])]
        return BuffConfig(
            buffs=[_san(v.split()) for v in self.buffs.get(1.0, tk.END).splitlines()] or None,
            interval=var_or_none(self.getvar('bot_config.buff.interval')),
        )

    def _clear(self):
        self.buffs.delete(1.0, tk.END)
