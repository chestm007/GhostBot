import tkinter as tk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import create_entry, create_int_slider
from GhostBot.UX import theme as T
from GhostBot.config import Config, PetConfig
from GhostBot.lib.var_or_none import var_or_none


class PetFrame(TabFrame):
    """Aba Pet -- DOIS tipos de pet, cada um com sua FLAG (decisao do dono):
    Pet do TAMER (combate: invoca/re-invoca/alimenta) e Pet NORMAL (so alimenta).
    Os campos de cada bloco aparecem quando a flag e' marcada."""

    def _init(self, *args, **kwargs) -> None:
        # ---- Flag + bloco do PET DO TAMER ----
        self._vars = dict(
            tamer_pet=create_entry(
                self, "Pet do Tamer (combate)", 0, 0, ("bot_config.pet.tamer_pet", bool),
                hint="Marque se este char é Tamer. O bot invoca, RE-INVOCA se o pet morrer e alimenta o pet do Tamer.",
            ),
        )
        self._tamer_box = tk.Frame(self, bg=T.BG_MAIN)
        self._tamer_box.grid(row=1, column=0, columnspan=10, sticky="w", padx=(16, 0))
        self._vars.update(
            spawn=create_entry(
                self._tamer_box, "Tecla Invocar:", 0, 0, ("bot_config.pet.spawn", str), entry_width=3,
                hint="Tecla que invoca/guarda o pet do Tamer (toggle). Re-invoca sozinho se o pet morrer.",
            ),
            food=create_entry(
                self._tamer_box, "Tecla Comida (Tamer):", 1, 0, ("bot_config.pet.food", str), entry_width=3,
                hint="Tecla da comida do pet do TAMER.",
            ),
            food_interval=create_int_slider(
                self._tamer_box, "Alimentar a cada:", 2, 0, "bot_config.pet.food_interval",
                default=5, min_val=1, max_val=60, suffix="min",
                hint="De quanto em quanto tempo alimenta o pet do Tamer (minutos).",
            ),
            respawn_interval=create_entry(
                self._tamer_box, "Re-invocar a cada (min):", 3, 0, ("bot_config.pet.respawn_interval", str), entry_width=4,
                hint="OPCIONAL: re-invoca de tempos em tempos (pet que expira sozinho). Vazio = só quando morrer.",
            ),
        )

        # ---- Flag + bloco do PET NORMAL ----
        self._vars['normal_pet'] = create_entry(
            self, "Pet normal (companheiro)", 2, 0, ("bot_config.pet.normal_pet", bool),
            hint="Marque se tem um pet NORMAL (não-combate) que precisa de comida. O bot só alimenta.",
        )
        self._normal_box = tk.Frame(self, bg=T.BG_MAIN)
        self._normal_box.grid(row=3, column=0, columnspan=10, sticky="w", padx=(16, 0))
        self._vars.update(
            normal_food=create_entry(
                self._normal_box, "Tecla Comida (normal):", 0, 0, ("bot_config.pet.normal_food", str), entry_width=3,
                hint="Tecla da comida do pet NORMAL (companheiro).",
            ),
            normal_food_interval=create_int_slider(
                self._normal_box, "Alimentar a cada:", 1, 0, "bot_config.pet.normal_food_interval",
                default=10, min_val=1, max_val=60, suffix="min",
                hint="De quanto em quanto tempo alimenta o pet normal (minutos).",
            ),
        )

        # mostra/esconde cada bloco conforme a flag (pega clique do usuario E load de config)
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
            self.setvar('bot_config.pet.respawn_interval', str(config.pet.spawn_interval_mins or ''))
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
            spawn_interval_mins=var_or_none(self.getvar('bot_config.pet.respawn_interval')),
            normal_pet=var_or_none(self.getvar('bot_config.pet.normal_pet'), bool),
            normal_food_interval_mins=var_or_none(self.getvar('bot_config.pet.normal_food_interval')),
        )
