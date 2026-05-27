from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import create_entry, create_int_slider
from GhostBot.config import Config, PetConfig
from GhostBot.lib.var_or_none import var_or_none


class PetFrame(TabFrame):
    """Aba Pet (Tamer) -- sustentacao do pet: invoca, alimenta e re-invoca se morrer.
    O combate (mandar o pet bater) fica na aba Attack (combo)."""

    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            spawn=create_entry(
                self, "Tecla Invocar:", 0, 0, ("bot_config.pet.spawn", str), entry_width=3,
                hint="Tecla que invoca/guarda o pet (toggle). O bot RE-INVOCA sozinho se o pet morrer.",
            ),
            food=create_entry(
                self, "Tecla Comida:", 1, 0, ("bot_config.pet.food", str), entry_width=3,
                hint="Tecla de alimentar o pet.",
            ),
            food_interval=create_int_slider(
                self, "Alimentar a cada:", 2, 0, "bot_config.pet.food_interval",
                default=5, min_val=1, max_val=60, suffix="min",
                hint="De quanto em quanto tempo o bot aperta a tecla de comida (minutos).",
            ),
            respawn_interval=create_entry(
                self, "Re-invocar a cada (min):", 3, 0, ("bot_config.pet.respawn_interval", str), entry_width=4,
                hint="OPCIONAL: re-invoca o pet de tempos em tempos (pet que expira sozinho). "
                     "Deixe VAZIO pra só re-invocar quando o pet morrer.",
            ),
        )

    def display_config(self, config: Config) -> None:
        if config.pet:
            b = config.pet.bindings or {}
            self.setvar('bot_config.pet.spawn', str(b.get('spawn', '') or ''))
            self.setvar('bot_config.pet.food', str(b.get('food', '') or ''))
            self.setvar('bot_config.pet.food_interval', str(config.pet.food_interval_mins or '5'))
            self.setvar('bot_config.pet.respawn_interval', str(config.pet.spawn_interval_mins or ''))
        else:
            self.clear()

    def extract_config(self) -> PetConfig:
        bindings = dict(
            spawn=self._nullable_string(self.getvar('bot_config.pet.spawn')),
            food=self._nullable_string(self.getvar('bot_config.pet.food')),
        )
        return PetConfig(
            bindings=self._populate_bindings(bindings),
            food_interval_mins=var_or_none(self.getvar('bot_config.pet.food_interval')),
            spawn_interval_mins=var_or_none(self.getvar('bot_config.pet.respawn_interval')),
        )
