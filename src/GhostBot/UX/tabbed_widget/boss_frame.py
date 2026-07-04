import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import create_entry, create_int_slider, ComboWidget
from GhostBot.UX import theme as T
from GhostBot.config import Config, BossConfig
from GhostBot.lib.var_or_none import var_or_none


HP_BG = T.HP_BG
MP_BG = T.MP_BG

ROLES = ["Tank", "DPS", "Fairy"]


class BossFrame(TabFrame):
    """Boss tab -- Cave Boss mode. The 'Role' (Tank/DPS/Fairy) is a dropdown; the fields
    below CHANGE according to the selected role. Step 1: functional Tank; DPS/Fairy remain
    as 'under construction' (we'll fill them in later steps)."""

    def _init(self, *args, **kwargs) -> None:
        self.grid_columnconfigure(11, weight=1)

        # ---- Role (dropdown) ----
        ttk.Label(self, text="Role:", anchor="w").grid(row=0, column=0, padx=4, pady=(6, 2), sticky="w")
        self._role_var = tk.StringVar(master=self, name="bot_config.boss.role_label", value="Tank")
        self._role_combo = ttk.Combobox(self, textvariable=self._role_var, values=ROLES,
                                         state="readonly", width=10)
        self._role_combo.grid(row=0, column=1, padx=2, pady=(6, 2), sticky="w")
        self._role_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_role_change())

        # ---- Common to Tank/DPS: boss name + attack combo ----
        self._common = tk.Frame(self, bg=T.BG_MAIN)
        self._common.grid(row=1, column=0, columnspan=12, sticky="ew")
        self._vars = dict(
            boss_name=create_entry(
                self._common, "Boss Name:", 0, 0, ("bot_config.boss.boss_name", str), entry_width=18,
                hint="Name (or part) of the boss. The bot TABs until it finds it and attacks ONLY it.",
            ),
        )
        ttk.Button(self._common, text="🎯 Grab Target", command=self._grab_target_name).grid(row=0, column=2, padx=4)
        self._combo = ComboWidget(
            self._common, "Combo:", grid_row=1, grid_column=0,
            hint="Sequence of keys the bot presses in a loop on the boss. Key + interval (ms).",
            show_tab_button=False,
        )
        self._combo.add_row()

        # ---- HP/MP Pots (DPS and Fairy; optional: blank key = disabled) ----
        # The TANK doesn't see this: in boss mode he DOESN'T pot -- Fairies heal the tank.
        self._pots_frame = tk.Frame(self, bg=T.BG_MAIN)
        self._pots_frame.grid(row=2, column=0, columnspan=12, sticky="ew")
        self._pots_frame.grid_columnconfigure(11, weight=1)
        hp_row = tk.Frame(self._pots_frame, bg=HP_BG)
        hp_row.grid(row=0, column=0, columnspan=12, sticky="ew", padx=2, pady=1)
        mp_row = tk.Frame(self._pots_frame, bg=MP_BG)
        mp_row.grid(row=1, column=0, columnspan=12, sticky="ew", padx=2, pady=1)
        self._vars.update(
            hp_low=create_int_slider(
                hp_row, "Pot HP at:", 0, 0, "bot_config.boss.battle_hp_low",
                default=30, min_val=0, max_val=100, suffix="%", bg=HP_BG,
                hint="HP below this % -> use the HP pot. Leave the key blank to disable.",
            ),
            hp_key=create_entry(
                hp_row, "HP Pot Key:", 0, 4, ("bot_config.boss.battle_hp_key", str), entry_width=3, bg=HP_BG,
                hint="HP pot key in combat. Blank = don't use.",
            ),
            mp_low=create_int_slider(
                mp_row, "Pot MP at:", 0, 0, "bot_config.boss.battle_mp_low",
                default=30, min_val=0, max_val=100, suffix="%", bg=MP_BG,
                hint="MP below this % -> use the MP pot. Leave the key blank to disable.",
            ),
            mp_key=create_entry(
                mp_row, "MP Pot Key:", 0, 4, ("bot_config.boss.battle_mp_key", str), entry_width=3, bg=MP_BG,
                hint="MP pot key in combat. Blank = don't use (Tank: leave empty, doesn't use MP).",
            ),
        )

        # ---- TANK block ----
        self._tank_frame = tk.Frame(self, bg=T.BG_MAIN)
        ttk.Label(self._tank_frame, text="— Tank —", anchor="w").grid(
            row=0, column=0, columnspan=4, sticky="w", padx=4, pady=(6, 2))
        self._vars.update(
            buff_interval=create_int_slider(
                self._tank_frame, "Buff every:", 1, 0, "bot_config.boss.buff_interval",
                default=30, min_val=5, max_val=300, suffix="s",
                hint="How often the tank re-applies buffs (seconds). Default 30s.",
            ),
        )
        self._tank_buffs = ComboWidget(
            self._tank_frame, "Tank buffs:", grid_row=2, grid_column=0,
            hint="Tank buffs (auto-applied: the bot just presses the key, without switching target). "
                 "Key + interval (ms).",
            show_tab_button=False,
        )
        self._tank_buffs.add_row()

        # ---- DPS / FAIRY blocks (placeholders -- next steps) ----
        self._dps_frame = tk.Frame(self, bg=T.BG_MAIN)
        ttk.Label(self._dps_frame, text="— DPS —", anchor="w").grid(
            row=0, column=0, columnspan=6, sticky="w", padx=4, pady=(6, 2))
        ttk.Label(
            self._dps_frame,
            text=("Hits non-stop on the boss (use Boss Name + Combo above).\n"
                  "• Aggro (automatic): if you lose HP in combat (= you pulled aggro), presses "
                  "F1 and waits to exit combat → the tank re-pulls → back to hitting.\n"
                  "• MP: configure the 'MP Pot' above — when it drops below %, retreat (F1), wait to exit "
                  "combat and take the pot."),
            anchor="w", foreground=T.FG_MUTED, justify="left", wraplength=580,
        ).grid(row=1, column=0, columnspan=8, sticky="w", padx=4, pady=(2, 4))
        self._fairy_frame = tk.Frame(self, bg=T.BG_MAIN)
        ttk.Label(self._fairy_frame, text="— Fairy —", anchor="w").grid(
            row=0, column=0, columnspan=4, sticky="w", padx=4, pady=(6, 2))
        self._vars.update(
            heal_key=create_entry(
                self._fairy_frame, "Heal Key:", 1, 0, ("bot_config.boss.heal_key", str), entry_width=3,
                hint="Heal skill key. The Fairy spams this key on the TARGET selected in the game.",
            ),
            heal_interval=create_int_slider(
                self._fairy_frame, "Heal every:", 2, 0, "bot_config.boss.heal_interval",
                default=2, min_val=1, max_val=15, suffix="s",
                hint="How often to press heal (seconds). ~2s = cast time.",
            ),
        )
        ttk.Label(self._fairy_frame,
                  text="Aim: the CURRENT TARGET — select in the game who to heal (the Fairy doesn't choose on its own).",
                  anchor="w", foreground=T.FG_MUTED).grid(row=3, column=0, columnspan=6, sticky="w", padx=4, pady=(4, 2))

        self._role_blocks = {"Tank": self._tank_frame, "DPS": self._dps_frame, "Fairy": self._fairy_frame}
        self._on_role_change()

    def _on_role_change(self) -> None:
        """Shows only the fields for the selected role."""
        role = self._role_var.get()
        for frame in self._role_blocks.values():
            frame.grid_forget()
        block = self._role_blocks.get(role)
        if block is not None:
            block.grid(row=3, column=0, columnspan=12, sticky="ew")
        # Fairy doesn't attack -> hide 'Boss Name' + 'Combo'
        if role == "Fairy":
            self._common.grid_remove()
        else:
            self._common.grid()
        # Tank DOESN'T pot in boss (Fairies heal) -> hide pots for Tank
        if role == "Tank":
            self._pots_frame.grid_remove()
        else:
            self._pots_frame.grid()

    def _grab_target_name(self) -> None:
        """Puts the target name selected in the game into the 'Boss Name' field (= Attack tab)."""
        name = (self.master.getvar('char_info.target_name') or '').strip()
        if name.lower() in ('', 'none', 'loading.', 'loading'):
            self._vars['boss_name'].set("(select a target in the game)")
            return
        self._vars['boss_name'].set(name)

    def display_config(self, config: Config) -> None:
        if config.boss:
            b = config.boss
            self._role_var.set((b.role or 'tank').capitalize())
            self.setvar('bot_config.boss.boss_name', b.boss_name or '')
            self._combo.set_attacks(b.attacks or [])

            hp_key = mp_key = ''
            if b.bindings:
                hp_key = str(b.bindings.get('battle_hp_pot', '') or '')
                mp_key = str(b.bindings.get('battle_mana_pot', '') or '')
            self.setvar('bot_config.boss.battle_hp_key', hp_key)
            self.setvar('bot_config.boss.battle_mp_key', mp_key)
            self.setvar('bot_config.boss.battle_hp_low', str(b.battle_hp_threshold or ''))
            self.setvar('bot_config.boss.battle_mp_low', str(b.battle_mana_threshold or ''))
            self.setvar('bot_config.boss.buff_interval',
                        str(int(b.buff_interval_secs)) if b.buff_interval_secs else '30')
            self._tank_buffs.set_attacks(b.buffs or [])

            heal_key = str(b.bindings.get('heal', '') or '') if b.bindings else ''
            self.setvar('bot_config.boss.heal_key', heal_key)
            self.setvar('bot_config.boss.heal_interval',
                        str(int(b.heal_interval_secs)) if b.heal_interval_secs else '2')
            self._on_role_change()
        else:
            self.clear()

    def extract_config(self) -> BossConfig:
        bindings = dict(
            battle_hp_pot=self._nullable_string(self.getvar('bot_config.boss.battle_hp_key')),
            battle_mana_pot=self._nullable_string(self.getvar('bot_config.boss.battle_mp_key')),
            heal=self._nullable_string(self.getvar('bot_config.boss.heal_key')),
        )
        return BossConfig(
            role=(self._role_var.get() or 'Tank').lower(),
            boss_name=var_or_none(self.getvar('bot_config.boss.boss_name')),
            attacks=self._combo.get_attacks() or None,
            bindings=self._populate_bindings(bindings),
            battle_hp_threshold=var_or_none(self.getvar('bot_config.boss.battle_hp_low')),
            battle_mana_threshold=var_or_none(self.getvar('bot_config.boss.battle_mp_low')),
            buffs=self._tank_buffs.get_attacks() or None,
            buff_interval_secs=var_or_none(self.getvar('bot_config.boss.buff_interval'), float),
            heal_interval_secs=var_or_none(self.getvar('bot_config.boss.heal_interval'), float),
        )

    def _clear(self) -> None:
        self._combo.set_attacks([])
        self._tank_buffs.set_attacks([])
        self._role_var.set("Tank")
        self._on_role_change()
