import time
import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.TabFrame import TabFrame
from GhostBot.client_window import ClientWindow
from GhostBot.config import Config, SellConfig
from GhostBot.lib.var_or_none import _str, _int, _tuple


class SellFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            item_pos=tk.StringVar(master=self, name="bot_config.sell.item_pos", value=''),
            npc_name=tk.StringVar(master=self, name="bot_config.sell.npc_name", value=''),
            interval_mins=tk.StringVar(master=self, name="bot_config.sell.interval_mins", value=''),
            npc_search_spot=tk.StringVar(master=self, name="bot_config.sell.npc_search_spot", value=''),
            return_spot=tk.StringVar(master=self, name="bot_config.sell.return_spot", value=''),
        )

        ttk.Label(master=self, text="Start item pos:", width=15).grid(row=0, column=0)
        ttk.Label(master=self, text="NPC name:", width=15).grid(row=1, column=0)
        ttk.Label(master=self, text="NPC search spot:", width=15).grid(row=2, column=0)
        ttk.Label(master=self, text="Interval mins:", width=15).grid(row=3, column=0)
        ttk.Label(master=self, text="Return Spot:", width=15).grid(row=4, column=0)

        tk.Entry(master=self, textvariable=self._vars["item_pos"], takefocus=False).grid(row=0, column=1)
        tk.Entry(master=self, textvariable=self._vars["npc_name"], takefocus=False).grid(row=1, column=1)
        tk.Entry(master=self, textvariable=self._vars["npc_search_spot"], takefocus=False).grid(row=2, column=1)
        tk.Entry(master=self, textvariable=self._vars["interval_mins"], takefocus=False).grid(row=3, column=1)
        tk.Entry(master=self, textvariable=self._vars["return_spot"], takefocus=False).grid(row=4, column=1)

        ttk.Button(
            master=self, text="Current", command=lambda: self._set_spot_as_current('npc_search_spot')
        ).grid(row=2, column=2)

        ttk.Button(
            master=self, text="Current", command=lambda: self._set_spot_as_current('return_spot')
        ).grid(row=4, column=2)

    def _set_spot_as_current(self, field: str) -> None:
        window_pos = self.getvar('window_info.pos')
        self._vars[field].set("Reading Mouse...")
        time.sleep(3)
        mouse_pos = ClientWindow.get_mouse_window_pos(window_pos)
        self._vars[field].set("{} {}".format(*mouse_pos))
        print(self.extract_config())

    def display_config(self, config: Config):
        def _format_spot(_spot):
            if _spot:
                return f"{' '.join(map(str, _spot))}"
            return ''

        if config.sell:
            self.setvar('bot_config.sell.item_pos', config.sell.sell_item_pos or '')
            self.setvar('bot_config.sell.npc_name', config.sell.sell_npc_name or '')
            self.setvar('bot_config.sell.interval_mins', config.sell.sell_interval_mins or '')
            self.setvar('bot_config.sell.npc_search_spot', _format_spot(config.sell.npc_search_spot))
            self.setvar('bot_config.sell.return_spot', _format_spot(config.sell.return_spot))

        else:
            self.clear()

    def extract_config(self) -> SellConfig:
        return SellConfig(
            sell_item_pos=_int(self.getvar('bot_config.sell.item_pos')),
            sell_npc_name=_str(self.getvar('bot_config.sell.npc_name')),
            sell_interval_mins=_int(self.getvar('bot_config.sell.interval_mins')),
            npc_search_spot=_tuple(self.getvar('bot_config.sell.npc_search_spot')),
            return_spot=_tuple(self.getvar('bot_config.sell.return_spot')),
        )
