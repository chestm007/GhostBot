from tkinter import ttk

from GhostBot.UX.tabbed_widget.TabFrame import TabFrame
from GhostBot.bot_controller import ExtendedClient
from GhostBot.config import Config, RegenConfig
from GhostBot.lib.var_or_none import _float, _tuple


class RegenFrame(TabFrame):
    def _init(self, client: ExtendedClient, *args, **kwargs) -> None:
        self.client = client
        self._vars = dict(
            hp_low=self._create_entry("HP Low:", 0, 0, ("bot_config.regen.hp_low", str)),
            hp_key=self._create_entry("HP Key:", 0, 2, ("bot_config.rege.hp_key", str)),
            mp_low=self._create_entry("MP Low:", 1, 0, ("bot_config.regen.mp_low", str)),
            mp_key=self._create_entry("MP Key:", 1, 2, ("bot_config.regen.mp_key", str)),
            sit_key=self._create_entry("Sit Key:", 2, 0, ("bot_config.regen.sit_key", str)),
            spot=self._create_entry("Spot:", 3, 0, ("bot_config.regen.spot", str)),
        )

        ttk.Button(
            master=self, text="Current", command=lambda: self._set_spot_as_current()
        ).grid(row=3, column=2)

    def _set_spot_as_current(self):
        self._vars['spot'].set(eval(self.master.getvar('char_info.position')))
        print(self.extract_config())

    def display_config(self, config: Config):
        def _format_spot(_spot):
            if _spot:
                return f"{' '.join(map(str, _spot))}"
            return ''

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
            self.setvar('bot_config.regen.spot', _format_spot(config.regen.spot))

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
            hp_threshold=_float(self.getvar('bot_config.regen.hp_low')),
            mana_threshold=_float(self.getvar('bot_config.regen.mp_low')),
            spot=_tuple(self.getvar('bot_config.regen.spot')),
        )
