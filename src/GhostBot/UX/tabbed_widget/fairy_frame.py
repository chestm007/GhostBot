import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import _format_spot, create_entry, create_int_slider, ComboWidget
from GhostBot.config import Config, FairyConfig
from GhostBot.lib.var_or_none import var_or_none
from GhostBot.UX import theme as T

HP_BG = T.HP_BG   # faixa HP (vermelho escuro)


class FairyFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        # Faixas vermelhas pros 2 thresholds de HP (team + self)
        team_row = tk.Frame(self, bg=HP_BG)
        team_row.grid(row=0, column=0, columnspan=12, sticky="ew", padx=2, pady=1)

        self_row = tk.Frame(self, bg=HP_BG)
        self_row.grid(row=1, column=0, columnspan=12, sticky="ew", padx=2, pady=1)

        # Espalha: faixas ocupam a largura toda; o campo da direita vai pra borda
        self.grid_columnconfigure(11, weight=1)
        team_row.grid_columnconfigure(3, weight=1)
        self_row.grid_columnconfigure(3, weight=1)

        self._vars = dict(
            heal_team=create_int_slider(
                team_row, "Curar time em:", 0, 0, "bot_config.fairy.heal_team",
                default=70, min_val=0, max_val=100, suffix="%",
                hint="Se o HP de algum membro do time cair abaixo desse %, a Fairy cura.",
                bg=HP_BG,
            ),
            heal_self=create_int_slider(
                self_row, "Curar a si em:", 0, 0, "bot_config.fairy.heal_self",
                default=60, min_val=0, max_val=100, suffix="%",
                hint="Se o HP da própria Fairy cair abaixo desse %, ela cura a si mesma.",
                bg=HP_BG,
            ),
            heal=create_entry(
                self, "Tecla Heal:", 2, 0, ("bot_config.fairy.heal", str), entry_width=3,
                hint="Tecla da skill de cura.",
            ),
            cure=create_entry(
                self, "Tecla Cure:", 3, 0, ("bot_config.fairy.cure", str), entry_width=3,
                hint="Tecla da skill HoT (cura menor que dura alguns segundos no aliado).",
            ),
            revive=create_entry(
                self, "Tecla Revive:", 4, 0, ("bot_config.fairy.revive", str), entry_width=3,
                hint="Tecla da skill que ressuscita aliados.",
            ),
            spot=create_entry(
                self, "Spot (X,Y):", 5, 0, ("bot_config.fairy.spot", str),
                hint="Coordenadas X,Y onde a Fairy fica parada. Botão 'Posição atual' captura sua posição agora.",
            ),
            buff_interval=create_int_slider(
                self, "Buffar time a cada:", 6, 0, "bot_config.fairy.buff_interval",
                default=15, min_val=1, max_val=60, suffix="min",
                hint="Frequência da rotina de buff de time (em minutos). Buffs duram 10-20 min, então 15 é bom default.",
            ),
            buff_self=create_entry(
                self, "Buffar a si:", 6, 4, ("bot_config.fairy.buff_self", bool),
                hint="Se marcado, a Fairy também aplica o combo de buffs em si mesma.",
            ),
        )

        ttk.Button(
            master=self, text="Posição atual", command=lambda: self._set_spot_as_current('spot')
        ).grid(row=5, column=2, padx=4)

        # Combo de buffs (sem botão TAB — buff não troca alvo)
        self._buff_combo = ComboWidget(
            self, "Buffs do time:", grid_row=7, grid_column=0,
            hint="Sequência de buffs aplicada em cada membro do time. Cada linha: tecla + intervalo ms.",
            show_tab_button=False,
        )
        self._buff_combo.add_row()

        # --- Modo Helper (cura + segue o aliado por tecla P; cross-PC, sem detectar) ---
        helper_row = tk.Frame(self, bg=T.BG_PANEL)
        helper_row.grid(row=8, column=0, columnspan=12, sticky="ew", padx=2, pady=(8, 2))
        self._vars['helper_mode'] = create_entry(
            helper_row, "Modo Helper:", 0, 0, ("bot_config.fairy.helper_mode", bool),
            hint="Liga o modo Helper: segue um aliado (tecla P) e cura sempre, só por tecla. "
                 "Selecione o char Helper na lista e dê Start — o bot faz o resto.",
        )
        self._vars['heal_interval'] = create_int_slider(
            helper_row, "Curar a cada:", 1, 0, "bot_config.fairy.heal_interval",
            default=2, min_val=1, max_val=15, suffix="s",
            hint="No modo Helper: aperta a tecla de cura a cada X segundos (e depois P, pra seguir).",
        )
        self._vars['follow'] = create_entry(
            helper_row, "Tecla Seguir:", 1, 4, ("bot_config.fairy.follow", str), entry_width=3,
            hint="Tecla que segue o aliado selecionado (padrão P).",
        )

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
            self.setvar('bot_config.fairy.buff_interval', str(config.fairy.buff_interval_mins or ''))
            self.setvar('bot_config.fairy.buff_self', bool(config.fairy.buff_self))
            self.setvar('bot_config.fairy.helper_mode', bool(config.fairy.helper_mode))
            self.setvar('bot_config.fairy.follow', str((config.fairy.bindings or {}).get('follow', '')))
            self.setvar('bot_config.fairy.heal_interval', str(config.fairy.heal_interval_secs or ''))
            self._buff_combo.set_attacks(config.fairy.buffs or [])
        else:
            self.clear()

    def extract_config(self) -> FairyConfig:
        bindings = dict(
            heal=self._nullable_string(self.getvar('bot_config.fairy.heal')),
            cure=self._nullable_string(self.getvar('bot_config.fairy.cure')),
            revive=self._nullable_string(self.getvar('bot_config.fairy.revive')),
            follow=self._nullable_string(self.getvar('bot_config.fairy.follow')),
        )
        return FairyConfig(
            bindings=self._populate_bindings(bindings),
            heal_team_threshold=var_or_none(self.getvar('bot_config.fairy.heal_team')),
            heal_self_threshold=var_or_none(self.getvar('bot_config.fairy.heal_self')),
            spot=var_or_none(self.getvar('bot_config.fairy.spot')),
            buffs=self._buff_combo.get_attacks() or None,
            buff_interval_mins=var_or_none(self.getvar('bot_config.fairy.buff_interval')),
            buff_self=var_or_none(self.getvar('bot_config.fairy.buff_self')),
            helper_mode=var_or_none(self.getvar('bot_config.fairy.helper_mode')),
            heal_interval_secs=var_or_none(self.getvar('bot_config.fairy.heal_interval')),
        )

    def _clear(self):
        self._buff_combo.set_attacks([])
