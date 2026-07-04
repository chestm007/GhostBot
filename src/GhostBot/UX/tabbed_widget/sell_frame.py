import time
from pathlib import Path
from tkinter import ttk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import _format_spot, create_entry, create_int_slider, NamedListWidget, setup_drag_from_listbox, widget_in_container
import tkinter as tk
from GhostBot.client_window import Win32ClientWindow
from GhostBot.config import Config, SellConfig
from GhostBot.lib.spot_capture import capture_map_offset
from GhostBot.lib.var_or_none import var_or_none
from GhostBot.UX import theme as T


_IMAGES_ROOT = Path(__file__).resolve().parent.parent.parent / "Images"


class SellFrame(TabFrame):
    def _init(self, client=None, *args, **kwargs) -> None:
        self._client = client  # IPC client, used by the 'Sell now' button
        self._vars = dict(
            item_pos=create_entry(
                self, "Starting slot (1-24):", 0, 0, ("bot_config.sell.item_pos", str), entry_width=8,
                hint="Slot number to start selling from (1 to 24, left to right, top to bottom). "
                     "Sells from this slot onward and KEEPS the previous ones. Ex: to keep slot 1, use 2.",
            ),
            use_mount=create_entry(
                self, "Use mount:", 0, 2, ("bot_config.sell.use_mount", bool),
                hint="If checked, the bot mounts up to travel to the NPC faster.",
            ),
            npc_name=create_entry(
                self, "NPC Name:", 1, 0, ("bot_config.sell.npc_name", str),
                hint="Exact name of the merchant NPC (must match what appears in the game).",
            ),
            mount_key=create_entry(
                self, "Mount Key:", 1, 2, ("bot_config.sell.mount_key", str), entry_width=3,
                hint="Key to mount/dismount.",
            ),
            npc_search_spot=create_entry(
                self, "NPC search spot:", 2, 0, ("bot_config.sell.npc_search_spot", str),
                hint="X,Y coordinates where the bot starts looking for the NPC. Use 'Current Position' to capture.",
            ),
            interval_mins=create_int_slider(
                self, "Sell every:", 3, 0, "bot_config.sell.interval_mins",
                default=30, min_val=5, max_val=120, suffix="min",
                hint="Frequency of the sell routine (in minutes). Only runs outside of combat.",
            ),
            return_spot_map_offset=create_entry(
                self, "Farm spot (map):", 4, 0, ("bot_config.sell.return_spot_map_offset", str),
                hint="Where to return after selling. Open the MAP (M) in the game, put the mouse on your farm spot "
                     "and click '📍 Capture Spot'. Without this the bot won't return to the spot.",
            ),
        )

        ttk.Button(
            master=self, text="Current Position", command=lambda: self._set_spot_as_current('npc_search_spot')
        ).grid(row=2, column=2, padx=4)

        # "Sell now" button — triggers the Sell routine once (bypasses interval).
        _now_btn = ttk.Button(
            master=self, text="🛒 Sell Now", style="Accent.TButton",
            command=self._on_sell_now,
        )
        _now_btn.grid(row=2, column=3, padx=4, pady=(2, 4), sticky="ew")
        from GhostBot.UX.utils import Tooltip as _Tooltip
        _Tooltip(_now_btn, "Triggers the Sell routine immediately, without waiting for the interval. "
                           "The char must be logged in, near the NPC, outside of combat. "
                           "Recommended to STOP the bot (Stop button) first to avoid click conflicts.")

        # Capture the farm spot on the MAP button (finds 'Map' title + reads cursor -> offset)
        ttk.Button(
            master=self, text="📍 Capture Spot", command=self._capture_map_spot
        ).grid(row=4, column=2, padx=4)

        # Important notice: game dialogs need to be visible/to the left
        _warn = tk.Label(
            self,
            text="⚠️ Keep game dialogs (NPC, sell, map) on the LEFT and VISIBLE. "
                 "If they spawn off-screen, the bot can't find them.",
            fg=T.GOLD, bg="#2E2410", wraplength=560, justify="left", anchor="w",
        )
        _warn.grid(row=5, column=0, columnspan=4, padx=4, pady=(6, 4), sticky="ew")

        # Bag items list (row 6) — source for drag-and-drop
        self._bag_frame = tk.Frame(self, bd=1, relief="solid", bg=T.BG_PANEL)
        self._bag_frame.grid(row=6, column=0, columnspan=3, padx=4, pady=(10, 2), sticky="ew")

        _bag_title = tk.Label(self._bag_frame, text="📜 Bag items — drag to category below",
                              bg=T.BG_PANEL, fg=T.FG_MAIN, font=("TkDefaultFont", 12, "bold"))
        _bag_title.pack(side="top", anchor="w", padx=8, pady=(6, 2))

        _bag_scroll_frame = tk.Frame(self._bag_frame, bg=T.BG_PANEL)
        _bag_scroll_frame.pack(side="top", fill="x", padx=8, pady=(0, 8))

        self._bag_listbox = tk.Listbox(_bag_scroll_frame, height=5, bg=T.BG_INPUT,
                                       borderwidth=0, highlightthickness=0,
                                       selectbackground=T.GREEN, selectforeground=T.BG_PANEL)
        self._bag_listbox.pack(side="left", fill="x", expand=True)

        _bag_scroll = tk.Scrollbar(_bag_scroll_frame, orient="vertical", command=self._bag_listbox.yview)
        _bag_scroll.pack(side="right", fill="y")
        self._bag_listbox.configure(yscrollcommand=_bag_scroll.set)

        # placeholder while name pointer not implemented
        self._bag_listbox.insert("end", "(inventory read pending — task #6)")
        self._bag_listbox.itemconfig(0, fg=T.FG_MUTED)

        # Item categorization (row 7) — destinations for drag-and-drop
        # capture_folder points to the folder where the item icon BMP will be saved when
        # the user captures via Win+Shift+S.
        self._items_trash = NamedListWidget(
            self, title="🗑️ Trash (sell)", grid_row=7, grid_column=0,
            title_color=T.FG_MUTED,
            hint="Items the bot will sell automatically when the inventory is full.",
            capture_folder=_IMAGES_ROOT / "SELL",
        )
        self._items_keep = NamedListWidget(
            self, title="📦 Good (keep)", grid_row=7, grid_column=1,
            title_color=T.GREEN_HI,
            hint="Valuable items the bot keeps in inventory without notifying.",
            capture_folder=_IMAGES_ROOT / "KEEP",
        )
        self._items_rare = NamedListWidget(
            self, title="✨ Super rare (alert)", grid_row=7, grid_column=2,
            title_color=T.GOLD,
            hint="Rare items that trigger a Discord alert when dropped.",
            capture_folder=_IMAGES_ROOT / "ALERTS" / "RARE",
        )

        # Drag-and-drop: drag from bag to one of the 3 categories
        setup_drag_from_listbox(self._bag_listbox, self._on_bag_drop)

    def _on_bag_drop(self, item_text, target_widget, source_idx):
        """Called when user drops a dragged item from the bag."""
        if item_text.startswith("("):  # placeholder
            return
        for target_list in (self._items_trash, self._items_keep, self._items_rare):
            if widget_in_container(target_widget, target_list.container):
                target_list.add_item(item_text)
                self._bag_listbox.delete(source_idx)
                return

    def update_bag_items(self, items: list[str]):
        """Called by main.py when bot sends INFO_CHAR with bag item list."""
        self._bag_listbox.delete(0, "end")
        if not items:
            self._bag_listbox.insert("end", "(inventory read pending — task #6)")
            self._bag_listbox.itemconfig(0, fg=T.FG_MUTED)
            return
        for it in items:
            self._bag_listbox.insert("end", it)

    def _on_sell_now(self) -> None:
        if self._client is None:
            return
        # char name comes from the dashboard (filled when user selects from the list)
        char = self.getvar('char_info.name')
        if not char or char == 'loading.':
            return
        self._client.sell_now(char)

    def _set_var_to_mouse_pos(self, field: str) -> None:
        window_pos = self.getvar('window_info.pos')
        self._vars[field].set("Reading mouse...")
        time.sleep(3)
        mouse_pos = Win32ClientWindow.get_mouse_window_pos(window_pos)
        self._vars[field].set("{} {}".format(*mouse_pos))

    def _set_spot_as_current(self, field: str):
        self._vars[field].set(self._parse_position(self.master.getvar('char_info.position')))

    def _capture_map_spot(self):
        """
        Finds the 'Map' title in the game window (template) and reads the cursor at the same
        instant -> saves the OFFSET (cursor_client - title). Same as calibrate.
        Open the MAP in the game and put the mouse on the spot before the timer runs out.
        """
        var = self._vars['return_spot_map_offset']
        var.set("Open the map and put the mouse on the spot...")
        self.update_idletasks()
        time.sleep(4)
        try:
            capture = capture_map_offset('map_title.bmp', threshold=0.70)
            if capture is None:
                var.set("(title 'Map' not found - is the map open/visible?)")
                return
            var.set("{} {}".format(capture.offset[0], capture.offset[1]))
        except Exception as e:
            var.set(f"(error: {e})")

    def display_config(self, config: Config):
        if config.sell:
            mount_key = ''
            if config.sell.bindings:
                mount_key = var_or_none(config.sell.bindings.get('mount'))
            self.setvar('bot_config.sell.item_pos', str(config.sell.sell_item_pos or ''))
            self.setvar('bot_config.sell.npc_name', str(config.sell.sell_npc_name or ''))
            self.setvar('bot_config.sell.interval_mins', str(config.sell.sell_interval_mins or ''))
            self.setvar('bot_config.sell.npc_search_spot', str(_format_spot(config.sell.npc_search_spot) or ''))
            self.setvar('bot_config.sell.return_spot_map_offset', str(_format_spot(config.sell.return_spot_map_offset) or ''))
            self.setvar('bot_config.sell.use_mount', str(bool(config.sell.use_mount)))
            self.setvar('bot_config.sell.mount_key', str(mount_key or ''))
            self._items_trash.set_items(config.sell.items_trash or [])
            self._items_keep.set_items(config.sell.items_keep or [])
            self._items_rare.set_items(config.sell.items_rare or [])
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
            return_spot_map_offset=var_or_none(self.getvar('bot_config.sell.return_spot_map_offset')),
            items_trash=self._items_trash.get_items() or None,
            items_keep=self._items_keep.get_items() or None,
            items_rare=self._items_rare.get_items() or None,
        )
