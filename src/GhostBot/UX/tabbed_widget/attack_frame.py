import time
import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import _format_spot, create_entry, create_int_slider, ComboWidget
from GhostBot.UX import theme as T
from GhostBot.config import Config, AttackConfig
from GhostBot.lib.var_or_none import var_or_none
from GhostBot.lib.spot_capture import capture_map_offset


HP_BG = T.HP_BG   # HP bar (dark red)
MP_BG = T.MP_BG   # MP bar (dark blue)


class AttackFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        # Class (dropdown): changes EXTRAS per class for farming. DPS (default) = current behavior.
        ttk.Label(self, text="Class:", anchor="w").grid(row=0, column=0, padx=4, pady=(6, 2), sticky="w")
        self._class_var = tk.StringVar(master=self, name="bot_config.attack.char_class_label", value="DPS")
        self._class_combo = ttk.Combobox(self, textvariable=self._class_var, values=["DPS", "Tamer", "Fairy"],
                                          state="readonly", width=10)
        self._class_combo.grid(row=0, column=1, padx=2, pady=(6, 2), sticky="w")
        self._class_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_class_change())

        # HP/MP range (POTS) — placed in rows 4-5 (canonical order: pots after combo)
        hp_row = tk.Frame(self, bg=HP_BG)
        hp_row.grid(row=4, column=0, columnspan=12, sticky="ew", padx=2, pady=1)

        # MP bar
        mp_row = tk.Frame(self, bg=MP_BG)
        mp_row.grid(row=5, column=0, columnspan=12, sticky="ew", padx=2, pady=1)

        # Spread: bars take full width; "Pot Key" goes to the right
        self.grid_columnconfigure(11, weight=1)
        hp_row.grid_columnconfigure(3, weight=1)
        mp_row.grid_columnconfigure(3, weight=1)

        self._vars = dict(
            hp_low=create_int_slider(
                hp_row, "Pot HP at:", 0, 0, "bot_config.attack.battle_hp_low",
                default=30, min_val=0, max_val=100, suffix="%",
                hint="When your HP drops below this %, the bot uses the HP pot in combat",
                bg=HP_BG,
            ),
            hp_key=create_entry(
                hp_row, "HP Pot Key:", 0, 4, ("bot_config.attack.battle_hp_key", str), entry_width=3,
                hint="Key to trigger HP pot in combat (when HP drops below %)",
                bg=HP_BG,
            ),
            mp_low=create_int_slider(
                mp_row, "Pot MP at:", 0, 0, "bot_config.attack.battle_mp_low",
                default=30, min_val=0, max_val=100, suffix="%",
                hint="When your MP drops below this %, the bot uses the MP pot in combat",
                bg=MP_BG,
            ),
            mp_key=create_entry(
                mp_row, "MP Pot Key:", 0, 4, ("bot_config.attack.battle_mp_key", str), entry_width=3,
                hint="Key to trigger MP pot in combat (when MP drops below %)",
                bg=MP_BG,
            ),
            stuck=create_int_slider(
                self, "No damage for (s):", 12, 0, "bot_config.attack.battle_stuck",
                default=8, min_val=1, max_val=10, suffix="s",
                hint="If target HP doesn't drop for this time, the bot considers stuck and switches targets",
            ),
            roam=create_int_slider(
                self, "Max distance from spot:", 11, 0, "bot_config.attack.battle_roam",
                default=40, min_val=15, max_val=100, suffix="u",
                hint="Farm radius around the Spot. If the character goes beyond this distance, it "
                     "re-centers on the Spot (small clicks on the minimap). 15=tightly stuck · 100=looser.",
            ),
            spot=create_entry(
                self, "Spot (X,Y):", 9, 0, ("bot_config.attack.spot", str),
                hint="X,Y coordinates of the farm point — measures distance to know when to return. "
                     "Filled by 'Current Position' or by '📍 Capture spot' below.",
            ),
            map_spot=create_entry(
                self, "Farm spot (map):", 10, 0, ("bot_config.attack.return_spot_map_offset", str),
                hint="WHERE the bot returns when it leaves the farm radius (click on the OPEN MAP). Stay at "
                     "the spot, open the MAP (M), put the mouse on your character on the map and click "
                     "'📍 Capture Spot'. It's the SAME as in the Sell tab (synced: change one, changes the other).",
            ),
            boss_lock=create_entry(
                self, "Lock onto Boss", 1, 0, ("bot_config.attack.boss_lock", bool),
                hint="If checked, the bot TABs until it finds the BOSS NAME (below) and attacks ONLY it "
                     "(ignores regular mobs). For boss runs.",
            ),
            boss_name=create_entry(
                self, "Boss Name:", 2, 0, ("bot_config.attack.boss_name", str), entry_width=18,
                hint="Name (or part) of the boss to lock onto. Ex.: 'Jing Gou'. Only works with "
                     "'Lock onto Boss' checked.",
            ),
        )

        # Dynamic combo: 1 empty row initially, user adds/removes
        self._combo = ComboWidget(
            self, "Combo:", grid_row=3, grid_column=0,
            hint="Sequence of keys the bot presses in a loop. Each row: key + interval in milliseconds. Add as many as you want.",
        )
        self._combo.add_row()  # 1 empty row to start

        ttk.Button(
            master=self, text="Current Position", command=lambda: self._set_spot_as_current('spot')
        ).grid(row=9, column=2, padx=4)

        ttk.Button(
            master=self, text="📍 Capture Spot", command=self._capture_farm_spot
        ).grid(row=10, column=2, padx=4)

        ttk.Button(
            master=self, text="🎯 Grab Target", command=self._grab_target_name
        ).grid(row=2, column=2, padx=4)

        # ---- Per-CLASS extras (appear as the dropdown changes) ----
        # Tamer: pet attack key. Fairy: heal key (used instead of HP pot).
        self._tamer_extra = tk.Frame(self, bg=T.BG_MAIN)
        self._tamer_extra.grid(row=8, column=0, columnspan=12, sticky="w")
        self._vars['pet_attack'] = create_entry(
            self._tamer_extra, "Pet attack key:", 0, 0, ("bot_config.attack.pet_attack", str), entry_width=3,
            hint="Tamer: key that orders the pet to attack. The bot presses it when grabbing EACH new target.",
        )
        self._fairy_extra = tk.Frame(self, bg=T.BG_MAIN)
        self._fairy_extra.grid(row=8, column=0, columnspan=12, sticky="w")
        self._vars['heal'] = create_entry(
            self._fairy_extra, "Heal Key:", 0, 0, ("bot_config.attack.heal", str), entry_width=3,
            hint="Fairy: when 'Pot HP at %' triggers, it presses THIS heal (instead of HP pot). MP follows the pot.",
        )

        # ---- Periodic buffs (came from the defunct Buff tab) ----
        self._vars['buff_interval'] = create_int_slider(
            self, "Buff every:", 6, 0, "bot_config.attack.buff_interval",
            default=15, min_val=1, max_val=60, suffix="min",
            hint="How often to reapply buffs (minutes). Buffs last ~10-20 min.",
        )
        self._buff_combo = ComboWidget(
            self, "Buffs:", grid_row=7, grid_column=0,
            hint="Sequence of buffs applied periodically (auto-buff, without switching target). Key + interval (ms).",
            show_tab_button=False,
        )
        self._buff_combo.add_row()

        self._on_class_change()

    def _on_class_change(self) -> None:
        """Shows extras for the selected class (Tamer = pet key; Fairy = heal key)."""
        cls = self._class_var.get()
        self._tamer_extra.grid_remove()
        self._fairy_extra.grid_remove()
        if cls == "Tamer":
            self._tamer_extra.grid()
        elif cls == "Fairy":
            self._fairy_extra.grid()

    def _set_spot_as_current(self, field: str):
        self._vars[field].set(self._parse_position(self.master.getvar('char_info.position')))

    def _grab_target_name(self):
        """Grabs the SELECTED target name from the game and puts it in the 'Boss Name' field
        (avoids typos). Reuses what the server already sends in char_info.target_name.
        No valid target -> warns in the field itself instead of pasting garbage."""
        name = (self.master.getvar('char_info.target_name') or '').strip()
        if name.lower() in ('', 'none', 'loading.', 'loading'):
            self._vars['boss_name'].set("(select a target in the game)")
            return
        self._vars['boss_name'].set(name)

    def _capture_farm_spot(self):
        """Captures the farm spot in one go: the X,Y position of the char (measures distance)
        AND the MAP offset (for map return, synced with the Sell tab).
        Stay at the spot, open the MAP (M), put the mouse on your character on the map, click."""
        # 1) Current X,Y of the char (to measure distance to the spot)
        try:
            self._set_spot_as_current('spot')
        except Exception:
            pass
        # 2) Map offset (for return click) -- same logic as the Sell tab
        var = self._vars['map_spot']
        var.set("Open the map (M) and put the mouse on the spot...")
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
        if config.attack:
            hp_key = mp_key = pet_key = heal_key = ''
            if config.attack.bindings:
                _b = config.attack.bindings
                hp_key = str(_b.get('battle_hp_pot', '') or '')
                mp_key = str(_b.get('battle_mana_pot', '') or '')
                pet_key = str(_b.get('pet_attack', '') or '')
                heal_key = str(_b.get('heal', '') or '')
            self.setvar('bot_config.attack.battle_hp_key', hp_key)
            self.setvar('bot_config.attack.battle_mp_key', mp_key)
            self.setvar('bot_config.attack.pet_attack', pet_key)
            self.setvar('bot_config.attack.heal', heal_key)
            self._class_var.set(
                {'dps': 'DPS', 'tamer': 'Tamer', 'fairy': 'Fairy'}.get(
                    (config.attack.char_class or 'dps').lower(), 'DPS'))
            self._on_class_change()

            self.setvar('bot_config.attack.battle_hp_low', str(config.attack.battle_hp_threshold or ''))
            self.setvar('bot_config.attack.battle_mp_low', str(config.attack.battle_mana_threshold or ''))
            self.setvar('bot_config.attack.battle_stuck', str(config.attack.stuck_interval or ''))
            self.setvar('bot_config.attack.battle_roam', str(config.attack.roam_distance or ''))
            self.setvar('bot_config.attack.spot', _format_spot(config.attack.spot))
            self.setvar('bot_config.attack.return_spot_map_offset',
                        _format_spot(config.attack.return_spot_map_offset))
            self.setvar('bot_config.attack.boss_lock', bool(config.attack.boss_lock))
            self.setvar('bot_config.attack.boss_name', config.attack.boss_name or '')

            self._combo.set_attacks(config.attack.attacks or [])
            self.setvar('bot_config.attack.buff_interval', str(config.attack.buff_interval_mins or '15'))
            self._buff_combo.set_attacks(config.attack.buffs or [])
        else:
            self.clear()

    def extract_config(self) -> AttackConfig:
        bindings = dict(
            battle_hp_pot=self._nullable_string(self.getvar('bot_config.attack.battle_hp_key')),
            battle_mana_pot=self._nullable_string(self.getvar('bot_config.attack.battle_mp_key')),
            pet_attack=self._nullable_string(self.getvar('bot_config.attack.pet_attack')),
            heal=self._nullable_string(self.getvar('bot_config.attack.heal')),
        )

        combo = self._combo.get_attacks()

        return AttackConfig(
            bindings=self._populate_bindings(bindings),
            attacks=combo or None,
            stuck_interval=var_or_none(self.getvar('bot_config.attack.battle_stuck')),
            battle_mana_threshold=var_or_none(self.getvar('bot_config.attack.battle_mp_low')),
            battle_hp_threshold=var_or_none(self.getvar('bot_config.attack.battle_hp_low')),
            roam_distance=var_or_none(self.getvar('bot_config.attack.battle_roam')),
            spot=var_or_none(self.getvar('bot_config.attack.spot')),
            return_spot_map_offset=var_or_none(self.getvar('bot_config.attack.return_spot_map_offset')),
            boss_lock=var_or_none(self.getvar('bot_config.attack.boss_lock')),
            boss_name=var_or_none(self.getvar('bot_config.attack.boss_name')),
            char_class=(self._class_var.get() or 'DPS').lower(),
            buffs=self._buff_combo.get_attacks() or None,
            buff_interval_mins=var_or_none(self.getvar('bot_config.attack.buff_interval')),
        )

    def _clear(self):
        self._combo.set_attacks([])
        self._buff_combo.set_attacks([])
