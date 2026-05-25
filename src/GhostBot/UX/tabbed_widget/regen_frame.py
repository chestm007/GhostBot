import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.controller.bot_controller import BotClientWindow
from GhostBot.config import Config, RegenConfig
from GhostBot.lib.var_or_none import var_or_none
from GhostBot.UX.utils import create_entry, create_int_slider, Tooltip
from GhostBot.UX import theme as T

HP_BG = T.HP_BG   # faixa HP (vermelho escuro)
MP_BG = T.MP_BG   # faixa MP (azul escuro)


class RegenFrame(TabFrame):
    def _init(self, client: BotClientWindow, *args, **kwargs) -> None:
        self.client = client

        # Faixa HP (fora de combate)
        hp_row = tk.Frame(self, bg=HP_BG)
        hp_row.grid(row=0, column=0, columnspan=12, sticky="ew", padx=2, pady=1)

        # Faixa MP (fora de combate)
        mp_row = tk.Frame(self, bg=MP_BG)
        mp_row.grid(row=1, column=0, columnspan=12, sticky="ew", padx=2, pady=1)

        # Espalha: faixas ocupam a largura toda; o "Tecla Pot" vai pra direita
        self.grid_columnconfigure(11, weight=1)
        hp_row.grid_columnconfigure(3, weight=1)
        mp_row.grid_columnconfigure(3, weight=1)

        self._vars = dict(
            hp_low=create_int_slider(
                hp_row, "Sentar com HP em:", 0, 0, "bot_config.regen.hp_low",
                default=60, min_val=0, max_val=100, suffix="%",
                hint="Fora de combate, se seu HP cair abaixo desse %, o bot senta pra regenerar",
                bg=HP_BG,
            ),
            hp_key=create_entry(
                hp_row, "Tecla Pot HP:", 0, 4, ("bot_config.regen.hp_key", str), entry_width=3,
                hint="Tecla do pot HP usado durante regen (opcional)",
                bg=HP_BG,
            ),
            mp_low=create_int_slider(
                mp_row, "Sentar com MP em:", 0, 0, "bot_config.regen.mp_low",
                default=60, min_val=0, max_val=100, suffix="%",
                hint="Fora de combate, se sua MP cair abaixo desse %, o bot senta pra regenerar",
                bg=MP_BG,
            ),
            mp_key=create_entry(
                mp_row, "Tecla Pot MP:", 0, 4, ("bot_config.regen.mp_key", str), entry_width=3,
                hint="Tecla do pot MP usado durante regen (opcional)",
                bg=MP_BG,
            ),
            sit_key=create_entry(
                self, "Tecla Sentar:", 2, 0, ("bot_config.regen.sit_key", str), entry_width=3,
                hint="Tecla pra sentar (regen passivo). Padrão TO: Insert",
            ),
        )

        # Classe sem mana (ex: Assassin): ignora o MP no descanso pra nao ficar preso sentado
        ignore_mana_var = tk.BooleanVar(
            master=self, name="bot_config.regen.ignore_mana", value=False
        )
        _ignore_cb = ttk.Checkbutton(
            master=self, text="Classe sem mana (ignora MP no descanso)",
            variable=ignore_mana_var,
        )
        _ignore_cb.grid(row=3, column=0, columnspan=6, padx=4, pady=4, sticky="w")
        Tooltip(_ignore_cb, "Marque para classes sem mana (ex: Assassin). O bot ignora o MP ao "
                            "descansar e não fica preso sentado esperando o MP encher.")
        self._vars['ignore_mana'] = ignore_mana_var

    def display_config(self, config: Config):

        if config.regen:
            hp_key = ''
            mp_key = ''
            sit_key = ''
            if config.regen.bindings:
                hp_key = str(config.regen.bindings.get('hp_pot', '') or '')
                mp_key = str(config.regen.bindings.get('mana_pot', '') or '')
                sit_key = str(config.regen.bindings.get('sit', '') or '')
            self.setvar('bot_config.regen.hp_key', hp_key)
            self.setvar('bot_config.regen.mp_key', mp_key)
            self.setvar('bot_config.regen.sit_key', sit_key)

            self.setvar('bot_config.regen.hp_low', str(config.regen.hp_threshold or ''))
            self.setvar('bot_config.regen.mp_low', str(config.regen.mana_threshold or ''))
            self._vars['ignore_mana'].set(bool(getattr(config.regen, 'ignore_mana', False)))

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
            ignore_mana=bool(self._vars['ignore_mana'].get()),
        )
