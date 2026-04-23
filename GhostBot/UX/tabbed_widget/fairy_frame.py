from tkinter import ttk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import _format_spot, create_entry
from GhostBot.config import Config, FairyConfig
from GhostBot.lib.var_or_none import var_or_none


class FairyFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            heal_team=create_entry(self, "Heal team at:", 0, 0, ("bot_config.fairy.heal_team", str)),
            heal_self=create_entry(self, "Heal self at:", 1, 0, ("bot_config.fairy.heal_self", str)),
            heal=create_entry(self, "Heal key:", 2, 0, ("bot_config.fairy.heal", str)),
            cure=create_entry(self, "Cure key:", 3, 0, ("bot_config.fairy.cure", str)),
            revive=create_entry(self, "Revive key:", 4, 0, ("bot_config.fairy.revive", str)),
            spot=create_entry(self, "Spot:", 5, 0, ("bot_config.fairy.spot", str)),
        )

        ttk.Button(
            master=self, text="Current", command=lambda: self._set_spot_as_current('spot')
        ).grid(row=5, column=2)

    def _set_spot_as_current(self, field: str):
        self._vars[field].set(eval(self.master.getvar('char_info.position')))


    def display_config(self, config: Config):
        if config.fairy:
            self.setvar('bot_config.fairy.heal_team', str(config.fairy.heal_team_threshold or ''))
            self.setvar('bot_config.fairy.heal_self', str(config.fairy.heal_self_threshold or ''))
            self.setvar('bot_config.fairy.heal', str((config.fairy.bindings or {}).get('heal', '')))
            self.setvar('bot_config.fairy.cure', str((config.fairy.bindings or {}).get('cure', '')))
            self.setvar('bot_config.fairy.revive', str((config.fairy.bindings or {}).get('revive', '')))
            self.setvar('bot_config.fairy.spot', _format_spot(config.fairy.spot))
        else:
            self.clear()

    def extract_config(self) -> FairyConfig:
        bindings = dict(
            heal=self._nullable_string(self.getvar('bot_config.fairy.heal')),
            cure=self._nullable_string(self.getvar('bot_config.fairy.cure')),
            revive=self._nullable_string(self.getvar('bot_config.fairy.revive')),
        )
        return FairyConfig(
            bindings=self._populate_bindings(bindings),
            heal_team_threshold=var_or_none(self.getvar('bot_config.fairy.heal_team')),
            heal_self_threshold=var_or_none(self.getvar('bot_config.fairy.heal_self')),
            spot=var_or_none(self.getvar('bot_config.fairy.spot')),
        )
