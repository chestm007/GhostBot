from GhostBot.UX.tabbed_widget.TabFrame import TabFrame
from GhostBot.config import Config, FairyConfig
from GhostBot.lib.var_or_none import _float


class FairyFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            heal_team=self._create_entry("Heal team at:", 0, 0, ("bot_config.fairy.heal_team", str)),
            heal_self=self._create_entry("Heal self at:", 1, 0, ("bot_config.fairy.heal_self", str)),
            heal=self._create_entry("Heal key:", 2, 0, ("bot_config.fairy.heal", str)),
            cure=self._create_entry("Cure key:", 3, 0, ("bot_config.fairy.cure", str)),
            revive=self._create_entry("Revive key:", 4, 0, ("bot_config.fairy.revive", str)),
        )

    def display_config(self, config: Config):
        if config.fairy:
            self.setvar('bot_config.fairy.heal_team', str(config.fairy.heal_team_threshold or ''))
            self.setvar('bot_config.fairy.heal_self', str(config.fairy.heal_self_threshold or ''))
            self.setvar('bot_config.fairy.heal', str((config.fairy.bindings or {}).get('heal', '')))
            self.setvar('bot_config.fairy.cure', str((config.fairy.bindings or {}).get('cure', '')))
            self.setvar('bot_config.fairy.revive', str((config.fairy.bindings or {}).get('revive', '')))
        else:
            self.clear()

    def extract_config(self) -> FairyConfig:
        _nullable_string = lambda x: x if x and x != 'None' else None
        bindings = dict(
            heal=_nullable_string(self.getvar('bot_config.fairy.heal')),
            cure=_nullable_string(self.getvar('bot_config.fairy.cure')),
            revive=_nullable_string(self.getvar('bot_config.fairy.revive')),
        )
        return FairyConfig(
            bindings=self._populate_bindings(bindings),
            heal_team_threshold=_float(self.getvar('bot_config.fairy.heal_team')),
            heal_self_threshold=_float(self.getvar('bot_config.fairy.heal_self')),
        )
