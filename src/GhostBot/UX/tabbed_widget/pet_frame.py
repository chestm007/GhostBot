from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.config import Config, PetConfig
from GhostBot.lib.var_or_none import var_or_none
from GhostBot.UX.utils import create_entry, create_int_slider


class PetFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            spawn_interval=create_int_slider(
                self, "Resummonar a cada:", 0, 0, "bot_config.pet.spawn_interval",
                default=10, min_val=1, max_val=60, suffix="min",
                hint="Frequência de re-summon do pet (em minutos). Cobre o caso do pet morrer ou desaparecer.",
            ),
            spawn_key=create_entry(
                self, "Tecla Summon:", 0, 4, ("bot_config.pet.spawn_key", str), entry_width=3,
                hint="Tecla pra invocar o pet (Tamer).",
            ),
            food_interval=create_int_slider(
                self, "Alimentar a cada:", 1, 0, "bot_config.pet.food_interval",
                default=10, min_val=1, max_val=60, suffix="min",
                hint="Frequência de alimentação do pet (em minutos). Mantém o pet vivo durante o farm.",
            ),
            food_key=create_entry(
                self, "Tecla Comida:", 1, 4, ("bot_config.pet.food_key", str), entry_width=3,
                hint="Tecla pra alimentar o pet (Tamer).",
            ),
        )

    def display_config(self, config: Config):
        if config.pet:
            self.setvar('bot_config.pet.spawn_interval', str(config.pet.spawn_interval_mins or ''))
            self.setvar('bot_config.pet.spawn_key', str((config.pet.bindings or {}).get('spawn', '')))
            self.setvar('bot_config.pet.food_interval', str(config.pet.food_interval_mins or ''))
            self.setvar('bot_config.pet.food_key', str((config.pet.bindings or {}).get('food', '')))
        else:
            self.clear()

    def extract_config(self) -> PetConfig:
        bindings = dict(
            spawn=self._nullable_string(self.getvar('bot_config.pet.spawn_key')),
            food=self._nullable_string(self.getvar('bot_config.pet.food_key')),
        )
        return PetConfig(
            bindings=self._populate_bindings(bindings),
            spawn_interval_mins=var_or_none(self.getvar('bot_config.pet.spawn_interval')),
            food_interval_mins=var_or_none(self.getvar('bot_config.pet.food_interval')),
        )
