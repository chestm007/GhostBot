import time
from tkinter import ttk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import _format_spot, create_entry
from GhostBot.client_window import Win32ClientWindow
from GhostBot.config import Config, SellConfig
from GhostBot.lib.var_or_none import var_or_none


class SellFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            item_pos=create_entry(self, "Start item pos:", 0, 0, ("bot_config.sell.item_pos", str)),
            use_mount=create_entry(self, "Use mount:", 0, 2, ("bot_config.sell.use_mount", bool)),
            npc_name=create_entry(self, "NPC name:", 1, 0, ("bot_config.sell.npc_name", str)),
            mount_key=create_entry(self, "Mount key:", 1, 2, ("bot_config.sell.mount_key", str)),
            npc_search_spot=create_entry(self, "NPC search spot:", 2, 0, ("bot_config.sell.npc_search_spot", str)),
            npc_sell_click_spot=create_entry(self, "NPC sell coords:", 3, 0, ("bot_config.sell.npc_sell_click_spot", str)),
            interval_mins=create_entry(self, "Interval mins:", 4, 0, ("bot_config.sell.interval_mins", str)),
        )

        ttk.Button(
            master=self, text="Current", command=lambda: self._set_spot_as_current('npc_search_spot')
        ).grid(row=2, column=2)

        ttk.Button(
            master=self, text="Current", command=lambda: self._set_var_to_mouse_pos('npc_sell_click_spot')
        ).grid(row=3, column=2)

    def _set_var_to_mouse_pos(self, field: str) -> None:
        window_pos = self.getvar('window_info.pos')
        self._vars[field].set("Reading Mouse...")
        time.sleep(3)
        mouse_pos = Win32ClientWindow.get_mouse_window_pos(window_pos)
        self._vars[field].set("{} {}".format(*mouse_pos))

    def _set_spot_as_current(self, field: str):
        self._vars[field].set(eval(self.master.getvar('char_info.position')))

    def display_config(self, config: Config):

        if config.sell:
            mount_key = ''
            if config.sell.bindings:
                mount_key = var_or_none(config.sell.bindings.get('mount'))
            self.setvar('bot_config.sell.item_pos', config.sell.sell_item_pos or '')
            self.setvar('bot_config.sell.npc_name', config.sell.sell_npc_name or '')
            self.setvar('bot_config.sell.interval_mins', config.sell.sell_interval_mins or '')
            self.setvar('bot_config.sell.npc_search_spot', _format_spot(config.sell.npc_search_spot))
            self.setvar('bot_config.sell.npc_sell_click_spot', _format_spot(config.sell.npc_sell_click_spot))
            self.setvar('bot_config.sell.use_mount', bool(config.sell.use_mount))
            self.setvar('bot_config.sell.mount_key', mount_key)

        else:
            self.clear()

    def extract_config(self) -> SellConfig:
        bindings = dict(
            mount=self._nullable_string(self.getvar('bot_config.sell.mount_key')),
        )
        return SellConfig(
            bindings=self._populate_bindings(bindings),
            sell_item_pos=var_or_none(self.getvar('bot_config.sell.item_pos')),
            sell_npc_name=var_or_none(self.getvar('bot_config.sell.npc_name')),
            use_mount=var_or_none(self.getvar('bot_config.sell.use_mount')),
            sell_interval_mins=var_or_none(self.getvar('bot_config.sell.interval_mins')),
            npc_search_spot=var_or_none(self.getvar('bot_config.sell.npc_search_spot')),
            npc_sell_click_spot=var_or_none(self.getvar('bot_config.sell.npc_sell_click_spot')),
        )
