from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.controller.bot_controller import BotClientWindow
from GhostBot.config import Config, RegenConfig
from GhostBot.lib.var_or_none import var_or_none
from GhostBot.UX.utils import create_entry


class RegenFrame(TabFrame):
    def _init(self, client: BotClientWindow, *args, **kwargs) -> None:
        self.client = client
        self._vars = dict(
            hp_low=create_entry(self, "HP Low:", 0, 0, ("bot_config.regen.hp_low", str)),
            hp_key=create_entry(self, "HP Key:", 0, 2, ("bot_config.rege.hp_key", str)),
            mp_low=create_entry(self, "MP Low:", 1, 0, ("bot_config.regen.mp_low", str)),
            mp_key=create_entry(self, "MP Key:", 1, 2, ("bot_config.regen.mp_key", str)),
            sit_key=create_entry(self, "Sit Key:", 2, 0, ("bot_config.regen.sit_key", str)),
        )

    def display_config(self, config: Config):

        if config.regen:
            hp_key = ''
            mp_key = ''
            sit_key = ''
            if config.regen.bindings:
                hp_key = str(config.regen.bindings.get('hp_pot'))
                mp_key = str(config.regen.bindings.get('mana_pot'))
                sit_key = str(config.regen.bindings.get('sit'))
            self.setvar('bot_config.regen.hp_key', hp_key)
            self.setvar('bot_config.regen.mp_key', mp_key)
            self.setvar('bot_config.regen.sit_key', sit_key)

            self.setvar('bot_config.regen.hp_low', str(config.regen.hp_threshold or ''))
            self.setvar('bot_config.regen.mp_low', str(config.regen.mana_threshold or ''))

        else:
            self.clear()

    def extract_config(self) -> RegenConfig:
        bindings = dict(
            hp_pot=self._nullable_string(self.getvar('bot_config.regen.hp_key')),
            mana_pot=self._nullable_string(self.getvar('bot_config.regen.mp_key')),
            sit=self._nullable_string(self.getvar('bot_config.regen.sit_key')),
        )
        return RegenConfig(
            bindings=self._populate_bindings(bindings),
            hp_threshold=var_or_none(self.getvar('bot_config.regen.hp_low')),
            mana_threshold=var_or_none(self.getvar('bot_config.regen.mp_low')),
        )
