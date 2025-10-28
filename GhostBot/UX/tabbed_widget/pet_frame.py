from GhostBot.UX.tabbed_widget.TabFrame import TabFrame
from GhostBot.config import Config, PetConfig
from GhostBot.lib.var_or_none import _int


class PetFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            spawn_interval=self._create_entry("Spawn interval:", 0, 0, ("bot_config.pet.spawn_interval", str)),
            spawn_key=self._create_entry("Spawn key:", 0, 2, ("bot_config.pet.spawn_key", str)),
            food_interval=self._create_entry("Feed interval:", 1, 0, ("bot_config.pet.food_interval", str)),
            food_key=self._create_entry("Feed key:",1, 2, ("bot_config.pet.food_key", str)),
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
        _nullable_string = lambda x: x if x and x != 'None' else None
        bindings = dict(
            spawn=_nullable_string(self.getvar('bot_config.pet.spawn_key')),
            food=_nullable_string(self.getvar('bot_config.pet.food_key')),
        )
        return PetConfig(
            bindings=self._populate_bindings(bindings),
            spawn_interval_mins=_int(self.getvar('bot_config.pet.spawn_interval')),
            food_interval_mins=_int(self.getvar('bot_config.pet.food_interval')),
        )
