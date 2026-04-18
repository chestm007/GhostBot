from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.config import Config, PetConfig
from GhostBot.lib.var_or_none import var_or_none
from UX.utils import create_entry


class PetFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            spawn_interval=create_entry(self, "Spawn interval:", 0, 0, ("bot_config.pet.spawn_interval", str)),
            spawn_key=create_entry(self, "Spawn key:", 0, 2, ("bot_config.pet.spawn_key", str)),
            food_interval=create_entry(self, "Feed interval:", 1, 0, ("bot_config.pet.food_interval", str)),
            food_key=create_entry(self, "Feed key:",1, 2, ("bot_config.pet.food_key", str)),
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
