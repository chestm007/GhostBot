import tkinter as tk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import create_entry, create_int_slider, ComboWidget
from GhostBot.config import Config, FairyConfig
from GhostBot.lib.var_or_none import var_or_none


class FairyFrame(TabFrame):
    """Aba Fairy -- Modo Helper (segue + cura um aliado por tecla, cross-PC)."""

    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            helper_mode=create_entry(
                self, "Modo Helper:", 0, 0, ("bot_config.fairy.helper_mode", bool),
                hint="Liga o modo Helper: a Fairy segue (tecla P) e cura sempre um aliado, "
                     "so por tecla. Selecione o aliado no jogo, a Fairy na lista, e de Start.",
            ),
            heal=create_entry(
                self, "Tecla Heal:", 1, 0, ("bot_config.fairy.heal", str), entry_width=3,
                hint="Tecla da skill de cura.",
            ),
            follow=create_entry(
                self, "Tecla Seguir:", 1, 4, ("bot_config.fairy.follow", str), entry_width=3,
                hint="Tecla que segue o alvo selecionado (padrao P).",
            ),
            heal_interval=create_int_slider(
                self, "Conjuração (s):", 2, 0, "bot_config.fairy.heal_interval",
                default=3, min_val=1, max_val=15, suffix="s",
                hint="Tempo de conjuração da cura + folga, ANTES de apertar o P (e de quanto em "
                     "quanto ela cura). A cura leva ~2s; o padrão 3s dá 1s de folga pra não "
                     "cortar o cast. Mude aqui se o jogo alterar o tempo de cast.",
            ),
            buff_interval=create_int_slider(
                self, "Buffar a cada:", 3, 0, "bot_config.fairy.buff_interval",
                default=15, min_val=1, max_val=60, suffix="min",
                hint="Frequência de re-buffar o aliado (em minutos). Buffs duram 10-20 min.",
            ),
        )

        # Combo de buffs (sem botão TAB -- buff não troca alvo)
        self._buff_combo = ComboWidget(
            self, "Buffs:", grid_row=4, grid_column=0,
            hint="Sequência de buffs aplicada no aliado. Cada linha: tecla + intervalo ms. "
                 "Após o combo, a Fairy aperta P de novo pra seguir.",
            show_tab_button=False,
        )
        self._buff_combo.add_row()

    def display_config(self, config: Config):
        if config.fairy:
            self.setvar('bot_config.fairy.helper_mode', bool(config.fairy.helper_mode))
            self.setvar('bot_config.fairy.heal', str((config.fairy.bindings or {}).get('heal', '')))
            self.setvar('bot_config.fairy.follow', str((config.fairy.bindings or {}).get('follow', '')))
            self.setvar('bot_config.fairy.heal_interval', str(config.fairy.heal_interval_secs or '3'))
            self.setvar('bot_config.fairy.buff_interval', str(config.fairy.buff_interval_mins or ''))
            self._buff_combo.set_attacks(config.fairy.buffs or [])
        else:
            self.clear()

    def extract_config(self) -> FairyConfig:
        bindings = dict(
            heal=self._nullable_string(self.getvar('bot_config.fairy.heal')),
            follow=self._nullable_string(self.getvar('bot_config.fairy.follow')),
        )
        return FairyConfig(
            bindings=self._populate_bindings(bindings),
            helper_mode=var_or_none(self.getvar('bot_config.fairy.helper_mode')),
            heal_interval_secs=var_or_none(self.getvar('bot_config.fairy.heal_interval'), float),
            buff_interval_mins=var_or_none(self.getvar('bot_config.fairy.buff_interval')),
            buffs=self._buff_combo.get_attacks() or None,
        )

    def _clear(self):
        self._buff_combo.set_attacks([])
