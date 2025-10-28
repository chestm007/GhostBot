import time
from tkinter import ttk

from GhostBot.UX.tabbed_widget.TabFrame import TabFrame
from GhostBot.client_window import ClientWindow
from GhostBot.config import Config, SellConfig
from GhostBot.lib.var_or_none import _str, _int, _tuple, _bool


class SellFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            item_pos=self._create_entry("Start item pos:", 0, 0, ("bot_config.sell.item_pos", str)),
            use_mount=self._create_entry("Use mount:", 0, 2, ("bot_config.sell.use_mount", bool)),
            npc_name=self._create_entry("NPC name:", 1, 0, ("bot_config.sell.npc_name", str)),
            mount_key=self._create_entry("Mount key:", 1, 2, ("bot_config.sell.mount_key", str)),
            npc_search_spot=self._create_entry("NPC search spot:", 2, 0, ("bot_config.sell.npc_search_spot", str)),
            interval_mins=self._create_entry("Interval mins:", 3, 0, ("bot_config.sell.interval_mins", str)),
            return_spot=self._create_entry("Return Spot:", 4, 0, ("bot_config.sell.return_spot", str)),
        )

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
            mount_key = ''
            if config.sell.bindings:
                mount_key = _str(config.sell.bindings.get('mount'))
            self.setvar('bot_config.sell.item_pos', config.sell.sell_item_pos or '')
            self.setvar('bot_config.sell.npc_name', config.sell.sell_npc_name or '')
            self.setvar('bot_config.sell.interval_mins', config.sell.sell_interval_mins or '')
            self.setvar('bot_config.sell.npc_search_spot', _format_spot(config.sell.npc_search_spot))
            self.setvar('bot_config.sell.return_spot', _format_spot(config.sell.return_spot))
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
            sell_item_pos=_int(self.getvar('bot_config.sell.item_pos')),
            sell_npc_name=_str(self.getvar('bot_config.sell.npc_name')),
            use_mount=_bool(self.getvar('bot_config.sell.use_mount')),
            sell_interval_mins=_int(self.getvar('bot_config.sell.interval_mins')),
            npc_search_spot=_tuple(self.getvar('bot_config.sell.npc_search_spot')),
            return_spot=_tuple(self.getvar('bot_config.sell.return_spot')),
        )
