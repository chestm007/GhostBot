import tkinter as tk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import create_entry, create_int_slider
from GhostBot.UX import theme as T
from GhostBot.config import Config, PetConfig
from GhostBot.lib.var_or_none import var_or_none


class PetFrame(TabFrame):
    """Pet tab -- TWO types of pet, each with its own FLAG (owner's decision):
    TAMER pet (combat: summon/re-summon/feed) and NORMAL pet (feed only).
    Each block's fields appear when the flag is checked."""

    def _init(self, *args, **kwargs) -> None:
        # ---- FLAG + TAMER PET block ----
        self._vars = dict(
            tamer_pet=create_entry(
                self, "Tamer's Pet (combat)", 0, 0, ("bot_config.pet.tamer_pet", bool),
                hint="Check if this char is a Tamer. The bot summons, RE-SUMMONS if the pet dies and feeds the Tamer's pet.",
            ),
        )
        self._tamer_box = tk.Frame(self, bg=T.BG_MAIN)
        self._tamer_box.grid(row=1, column=0, columnspan=10, sticky="w", padx=(16, 0))
        self._vars.update(
            spawn=create_entry(
                self._tamer_box, "Summon Key:", 0, 0, ("bot_config.pet.spawn", str), entry_width=3,
                hint="Key that summons/puts away the Tamer's pet (toggle). Re-summons automatically if the pet dies.",
            ),
            food=create_entry(
                self._tamer_box, "Feed Key (Tamer):", 1, 0, ("bot_config.pet.food", str), entry_width=3,
                hint="Pet food key for the TAMER.",
            ),
            food_interval=create_int_slider(
                self._tamer_box, "Feed every:", 2, 0, "bot_config.pet.food_interval",
                default=5, min_val=1, max_val=60, suffix="min",
                hint="How often to feed the Tamer's pet (minutes).",
            ),
        )

        # ---- FLAG + NORMAL PET block ----
        self._vars['normal_pet'] = create_entry(
            self, "Normal pet (companion)", 2, 0, ("bot_config.pet.normal_pet", bool),
            hint="Check if you have a NORMAL pet (non-combat) that needs food. The bot only feeds it.",
        )
        self._normal_box = tk.Frame(self, bg=T.BG_MAIN)
        self._normal_box.grid(row=3, column=0, columnspan=10, sticky="w", padx=(16, 0))
        self._vars.update(
            normal_food=create_entry(
                self._normal_box, "Feed Key (normal):", 0, 0, ("bot_config.pet.normal_food", str), entry_width=3,
                hint="Pet food key for the NORMAL pet (companion).",
            ),
            normal_food_interval=create_int_slider(
                self._normal_box, "Feed every:", 1, 0, "bot_config.pet.normal_food_interval",
                default=10, min_val=1, max_val=60, suffix="min",
                hint="How often to feed the normal pet (minutes).",
            ),
        )

        # show/hide each block according to the flag (catches user click AND config load)
        self._vars['tamer_pet'].trace_add('write', lambda *a: self._sync_sections())
        self._vars['normal_pet'].trace_add('write', lambda *a: self._sync_sections())
        self._sync_sections()

    def _sync_sections(self) -> None:
        (self._tamer_box.grid if self._vars['tamer_pet'].get() else self._tamer_box.grid_remove)()
        (self._normal_box.grid if self._vars['normal_pet'].get() else self._normal_box.grid_remove)()

    def display_config(self, config: Config) -> None:
        if config.pet:
            b = config.pet.bindings or {}
            self.setvar('bot_config.pet.tamer_pet', bool(config.pet.tamer_pet))
            self.setvar('bot_config.pet.spawn', str(b.get('spawn', '') or ''))
            self.setvar('bot_config.pet.food', str(b.get('food', '') or ''))
            self.setvar('bot_config.pet.food_interval', str(config.pet.food_interval_mins or '5'))
            self.setvar('bot_config.pet.normal_pet', bool(config.pet.normal_pet))
            self.setvar('bot_config.pet.normal_food', str(b.get('normal_food', '') or ''))
            self.setvar('bot_config.pet.normal_food_interval', str(config.pet.normal_food_interval_mins or '10'))
            self._sync_sections()
        else:
            self.clear()
            self._sync_sections()

    def extract_config(self) -> PetConfig:
        bindings = dict(
            spawn=self._nullable_string(self.getvar('bot_config.pet.spawn')),
            food=self._nullable_string(self.getvar('bot_config.pet.food')),
            normal_food=self._nullable_string(self.getvar('bot_config.pet.normal_food')),
        )
        return PetConfig(
            bindings=self._populate_bindings(bindings),
            tamer_pet=var_or_none(self.getvar('bot_config.pet.tamer_pet'), bool),
            food_interval_mins=var_or_none(self.getvar('bot_config.pet.food_interval')),
            normal_pet=var_or_none(self.getvar('bot_config.pet.normal_pet'), bool),
            normal_food_interval_mins=var_or_none(self.getvar('bot_config.pet.normal_food_interval')),
        )
