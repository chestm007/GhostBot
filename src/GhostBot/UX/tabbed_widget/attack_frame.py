import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import _format_spot, create_entry, create_int_slider, ComboWidget
from GhostBot.UX import theme as T
from GhostBot.config import Config, AttackConfig
from GhostBot.lib.var_or_none import var_or_none


HP_BG = T.HP_BG   # faixa HP (vermelho escuro)
MP_BG = T.MP_BG   # faixa MP (azul escuro)


class AttackFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        # Faixa HP — Frame inteiro colorido, widgets dentro
        hp_row = tk.Frame(self, bg=HP_BG)
        hp_row.grid(row=0, column=0, columnspan=12, sticky="ew", padx=2, pady=1)

        # Faixa MP
        mp_row = tk.Frame(self, bg=MP_BG)
        mp_row.grid(row=1, column=0, columnspan=12, sticky="ew", padx=2, pady=1)

        # Espalha: faixas ocupam a largura toda; o "Tecla Pot" vai pra direita
        self.grid_columnconfigure(11, weight=1)
        hp_row.grid_columnconfigure(3, weight=1)
        mp_row.grid_columnconfigure(3, weight=1)

        self._vars = dict(
            hp_low=create_int_slider(
                hp_row, "Pot HP em:", 0, 0, "bot_config.attack.battle_hp_low",
                default=30, min_val=0, max_val=100, suffix="%",
                hint="Quando seu HP cair abaixo desse %, o bot usa o pot HP em combate",
                bg=HP_BG,
            ),
            hp_key=create_entry(
                hp_row, "Tecla Pot HP:", 0, 4, ("bot_config.attack.battle_hp_key", str), entry_width=3,
                hint="Tecla pra acionar pot HP em combate (quando HP cair abaixo do %)",
                bg=HP_BG,
            ),
            mp_low=create_int_slider(
                mp_row, "Pot MP em:", 0, 0, "bot_config.attack.battle_mp_low",
                default=30, min_val=0, max_val=100, suffix="%",
                hint="Quando sua MP cair abaixo desse %, o bot usa o pot MP em combate",
                bg=MP_BG,
            ),
            mp_key=create_entry(
                mp_row, "Tecla Pot MP:", 0, 4, ("bot_config.attack.battle_mp_key", str), entry_width=3,
                hint="Tecla pra acionar pot MP em combate (quando MP cair abaixo do %)",
                bg=MP_BG,
            ),
            stuck=create_int_slider(
                self, "Sem dano por (s):", 2, 0, "bot_config.attack.battle_stuck",
                default=8, min_val=1, max_val=10, suffix="s",
                hint="Se o HP do alvo não cair por esse tempo, o bot considera travado e troca de alvo",
            ),
            roam=create_int_slider(
                self, "Distância máx do spot:", 3, 0, "bot_config.attack.battle_roam",
                default=60, min_val=40, max_val=100, suffix="un",
                hint="Raio do círculo de farm ao redor do Spot. 40=bem preso · 100=mais solto. "
                     "Se o personagem sair do raio, ele volta ao Spot.",
            ),
            spot=create_entry(
                self, "Spot (X,Y):", 5, 0, ("bot_config.attack.spot", str),
                hint="Coordenadas X,Y do ponto fixo de farm. Botão 'Posição atual' captura sua posição agora.",
            ),
        )

        # Combo dinâmico: 1 linha vazia inicialmente, usuário adiciona/remove
        self._combo = ComboWidget(
            self, "Combo:", grid_row=4, grid_column=0,
            hint="Sequência de teclas que o bot aperta em loop. Cada linha: tecla + intervalo em milissegundos. Adicione quantas quiser.",
        )
        self._combo.add_row()  # 1 linha vazia pra começar

        ttk.Button(
            master=self, text="Posição atual", command=lambda: self._set_spot_as_current('spot')
        ).grid(row=5, column=2, padx=4)

    def _set_spot_as_current(self, field: str):
        self._vars[field].set(eval(self.master.getvar('char_info.position')))

    def display_config(self, config: Config):
        if config.attack:
            hp_key = ''
            mp_key = ''
            if config.attack.bindings:
                hp_key = str(config.attack.bindings.get('battle_hp_pot', ''))
                mp_key = str(config.attack.bindings.get('battle_mana_pot', ''))
            self.setvar('bot_config.attack.battle_hp_key', hp_key)
            self.setvar('bot_config.attack.battle_mp_key', mp_key)

            self.setvar('bot_config.attack.battle_hp_low', str(config.attack.battle_hp_threshold or ''))
            self.setvar('bot_config.attack.battle_mp_low', str(config.attack.battle_mana_threshold or ''))
            self.setvar('bot_config.attack.battle_stuck', str(config.attack.stuck_interval or ''))
            self.setvar('bot_config.attack.battle_roam', str(config.attack.roam_distance or ''))
            self.setvar('bot_config.attack.spot', _format_spot(config.attack.spot))

            self._combo.set_attacks(config.attack.attacks or [])
        else:
            self.clear()

    def extract_config(self) -> AttackConfig:
        bindings = dict(
            battle_hp_pot=self._nullable_string(self.getvar('bot_config.attack.battle_hp_key')),
            battle_mana_pot=self._nullable_string(self.getvar('bot_config.attack.battle_mp_key')),
        )

        combo = self._combo.get_attacks()

        return AttackConfig(
            bindings=self._populate_bindings(bindings),
            attacks=combo or None,
            stuck_interval=var_or_none(self.getvar('bot_config.attack.battle_stuck')),
            battle_mana_threshold=var_or_none(self.getvar('bot_config.attack.battle_mp_low')),
            battle_hp_threshold=var_or_none(self.getvar('bot_config.attack.battle_hp_low')),
            roam_distance=var_or_none(self.getvar('bot_config.attack.battle_roam')),
            spot=var_or_none(self.getvar('bot_config.attack.spot')),
        )

    def _clear(self):
        self._combo.set_attacks([])
