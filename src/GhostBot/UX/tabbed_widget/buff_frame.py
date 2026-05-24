import tkinter as tk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.config import Config, BuffConfig
from GhostBot.lib.var_or_none import var_or_none
from GhostBot.UX.utils import create_int_slider, ComboWidget


class BuffFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            interval=create_int_slider(
                self, "Re-buffar a cada:", 0, 0, "bot_config.buff.interval",
                default=15, min_val=1, max_val=60, suffix="min",
                hint="Frequência de aplicação dos buffs (em minutos). Buffs do TO duram 10-20 min normalmente.",
            ),
        )

        # Combo de buffs (mesma estrutura do Attack combo, sem botão TAB — buff não troca alvo)
        self._combo = ComboWidget(
            self, "Buffs:", grid_row=1, grid_column=0,
            hint="Sequência de buffs a aplicar. Cada linha: tecla + intervalo em ms (tempo entre apertos).",
            show_tab_button=False,
        )
        self._combo.add_row()

    def display_config(self, config: Config):
        if config.buff:
            self.setvar('bot_config.buff.interval', str(config.buff.interval or ''))
            self._combo.set_attacks(config.buff.buffs or [])
        else:
            self.clear()

    def extract_config(self) -> BuffConfig:
        return BuffConfig(
            buffs=self._combo.get_attacks() or None,
            interval=var_or_none(self.getvar('bot_config.buff.interval')),
        )

    def _clear(self):
        self._combo.set_attacks([])
