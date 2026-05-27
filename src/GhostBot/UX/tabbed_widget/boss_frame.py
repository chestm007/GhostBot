import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import create_entry, create_int_slider, ComboWidget
from GhostBot.UX import theme as T
from GhostBot.config import Config, BossConfig
from GhostBot.lib.var_or_none import var_or_none


HP_BG = T.HP_BG
MP_BG = T.MP_BG

ROLES = ["Tank", "DPS", "Fairy"]


class BossFrame(TabFrame):
    """Aba Boss -- modo Cave Boss. O 'Papel' (Tank/DPS/Fairy) e' um dropdown; os campos
    de baixo MUDAM conforme o papel escolhido. Passo 1: Tank funcional; DPS/Fairy ficam
    como 'em construcao' (a gente preenche nos proximos passos)."""

    def _init(self, *args, **kwargs) -> None:
        self.grid_columnconfigure(11, weight=1)

        # ---- Papel (dropdown) ----
        ttk.Label(self, text="Papel:", anchor="w").grid(row=0, column=0, padx=4, pady=(6, 2), sticky="w")
        self._role_var = tk.StringVar(master=self, name="bot_config.boss.role_label", value="Tank")
        self._role_combo = ttk.Combobox(self, textvariable=self._role_var, values=ROLES,
                                         state="readonly", width=10)
        self._role_combo.grid(row=0, column=1, padx=2, pady=(6, 2), sticky="w")
        self._role_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_role_change())

        # ---- Comum a Tank/DPS: nome do boss + combo de ataque ----
        self._common = tk.Frame(self, bg=T.BG_MAIN)
        self._common.grid(row=1, column=0, columnspan=12, sticky="ew")
        self._vars = dict(
            boss_name=create_entry(
                self._common, "Nome do Boss:", 0, 0, ("bot_config.boss.boss_name", str), entry_width=18,
                hint="Nome (ou parte) do boss. O bot da TAB ate achar e ataca SO ele.",
            ),
        )
        ttk.Button(self._common, text="🎯 Pegar alvo", command=self._grab_target_name).grid(row=0, column=2, padx=4)
        self._combo = ComboWidget(
            self._common, "Combo:", grid_row=1, grid_column=0,
            hint="Sequencia de teclas que o bot aperta em loop no boss. Tecla + intervalo (ms).",
            show_tab_button=False,
        )
        self._combo.add_row()

        # ---- Pots HP/MP (comuns, opcionais: tecla em branco = desligado) ----
        pots = tk.Frame(self, bg=T.BG_MAIN)
        pots.grid(row=2, column=0, columnspan=12, sticky="ew")
        pots.grid_columnconfigure(11, weight=1)
        hp_row = tk.Frame(pots, bg=HP_BG)
        hp_row.grid(row=0, column=0, columnspan=12, sticky="ew", padx=2, pady=1)
        mp_row = tk.Frame(pots, bg=MP_BG)
        mp_row.grid(row=1, column=0, columnspan=12, sticky="ew", padx=2, pady=1)
        self._vars.update(
            hp_low=create_int_slider(
                hp_row, "Pot HP em:", 0, 0, "bot_config.boss.battle_hp_low",
                default=30, min_val=0, max_val=100, suffix="%", bg=HP_BG,
                hint="HP abaixo desse % -> usa o pot HP. Deixe a tecla em branco pra desligar.",
            ),
            hp_key=create_entry(
                hp_row, "Tecla Pot HP:", 0, 4, ("bot_config.boss.battle_hp_key", str), entry_width=3, bg=HP_BG,
                hint="Tecla do pot HP em combate. Em branco = nao usa.",
            ),
            mp_low=create_int_slider(
                mp_row, "Pot MP em:", 0, 0, "bot_config.boss.battle_mp_low",
                default=30, min_val=0, max_val=100, suffix="%", bg=MP_BG,
                hint="MP abaixo desse % -> usa o pot MP. Deixe a tecla em branco pra desligar.",
            ),
            mp_key=create_entry(
                mp_row, "Tecla Pot MP:", 0, 4, ("bot_config.boss.battle_mp_key", str), entry_width=3, bg=MP_BG,
                hint="Tecla do pot MP em combate. Em branco = nao usa (Tank: deixe vazio, nao usa MP).",
            ),
        )

        # ---- Bloco TANK ----
        self._tank_frame = tk.Frame(self, bg=T.BG_MAIN)
        ttk.Label(self._tank_frame, text="— Tank —", anchor="w").grid(
            row=0, column=0, columnspan=4, sticky="w", padx=4, pady=(6, 2))
        self._vars.update(
            buff_interval=create_int_slider(
                self._tank_frame, "Buffar a cada:", 1, 0, "bot_config.boss.buff_interval",
                default=30, min_val=5, max_val=300, suffix="s",
                hint="De quanto em quanto tempo o tank reaplica os buffs (segundos). Padrao 30s.",
            ),
        )
        self._tank_buffs = ComboWidget(
            self._tank_frame, "Buffs do tank:", grid_row=2, grid_column=0,
            hint="Buffs do tank (auto-aplicados: o bot so aperta a tecla, sem trocar de alvo). "
                 "Tecla + intervalo (ms).",
            show_tab_button=False,
        )
        self._tank_buffs.add_row()

        # ---- Blocos DPS / FAIRY (placeholders -- proximos passos) ----
        self._dps_frame = tk.Frame(self, bg=T.BG_MAIN)
        ttk.Label(self._dps_frame, text="— DPS — (em construção: controle de aggro + recuperar MP)",
                  anchor="w", foreground=T.FG_MUTED).grid(row=0, column=0, sticky="w", padx=4, pady=6)
        self._fairy_frame = tk.Frame(self, bg=T.BG_MAIN)
        ttk.Label(self._fairy_frame, text="— Fairy —", anchor="w").grid(
            row=0, column=0, columnspan=4, sticky="w", padx=4, pady=(6, 2))
        self._vars.update(
            heal_key=create_entry(
                self._fairy_frame, "Tecla de Cura:", 1, 0, ("bot_config.boss.heal_key", str), entry_width=3,
                hint="Tecla da skill de cura. A Fairy spama essa tecla no ALVO selecionado no jogo.",
            ),
            heal_interval=create_int_slider(
                self._fairy_frame, "Curar a cada:", 2, 0, "bot_config.boss.heal_interval",
                default=2, min_val=1, max_val=15, suffix="s",
                hint="De quanto em quanto tempo aperta a cura (segundos). ~2s = tempo do cast.",
            ),
        )
        ttk.Label(self._fairy_frame,
                  text="Mira: o ALVO atual — selecione no jogo quem curar (a Fairy não escolhe sozinha).",
                  anchor="w", foreground=T.FG_MUTED).grid(row=3, column=0, columnspan=6, sticky="w", padx=4, pady=(4, 2))

        self._role_blocks = {"Tank": self._tank_frame, "DPS": self._dps_frame, "Fairy": self._fairy_frame}
        self._on_role_change()

    def _on_role_change(self) -> None:
        """Mostra so os campos do papel selecionado."""
        role = self._role_var.get()
        for frame in self._role_blocks.values():
            frame.grid_forget()
        block = self._role_blocks.get(role)
        if block is not None:
            block.grid(row=3, column=0, columnspan=12, sticky="ew")
        # Fairy nao ataca -> esconde 'Nome do Boss' + 'Combo'
        if role == "Fairy":
            self._common.grid_remove()
        else:
            self._common.grid()

    def _grab_target_name(self) -> None:
        """Poe o nome do alvo selecionado no jogo no campo 'Nome do Boss' (= aba Attack)."""
        name = (self.master.getvar('char_info.target_name') or '').strip()
        if name.lower() in ('', 'none', 'loading.', 'loading'):
            self._vars['boss_name'].set("(selecione um alvo no jogo)")
            return
        self._vars['boss_name'].set(name)

    def display_config(self, config: Config) -> None:
        if config.boss:
            b = config.boss
            self._role_var.set((b.role or 'tank').capitalize())
            self.setvar('bot_config.boss.boss_name', b.boss_name or '')
            self._combo.set_attacks(b.attacks or [])

            hp_key = mp_key = ''
            if b.bindings:
                hp_key = str(b.bindings.get('battle_hp_pot', '') or '')
                mp_key = str(b.bindings.get('battle_mana_pot', '') or '')
            self.setvar('bot_config.boss.battle_hp_key', hp_key)
            self.setvar('bot_config.boss.battle_mp_key', mp_key)
            self.setvar('bot_config.boss.battle_hp_low', str(b.battle_hp_threshold or ''))
            self.setvar('bot_config.boss.battle_mp_low', str(b.battle_mana_threshold or ''))
            self.setvar('bot_config.boss.buff_interval',
                        str(int(b.buff_interval_secs)) if b.buff_interval_secs else '30')
            self._tank_buffs.set_attacks(b.buffs or [])

            heal_key = str(b.bindings.get('heal', '') or '') if b.bindings else ''
            self.setvar('bot_config.boss.heal_key', heal_key)
            self.setvar('bot_config.boss.heal_interval',
                        str(int(b.heal_interval_secs)) if b.heal_interval_secs else '2')
            self._on_role_change()
        else:
            self.clear()

    def extract_config(self) -> BossConfig:
        bindings = dict(
            battle_hp_pot=self._nullable_string(self.getvar('bot_config.boss.battle_hp_key')),
            battle_mana_pot=self._nullable_string(self.getvar('bot_config.boss.battle_mp_key')),
            heal=self._nullable_string(self.getvar('bot_config.boss.heal_key')),
        )
        return BossConfig(
            role=(self._role_var.get() or 'Tank').lower(),
            boss_name=var_or_none(self.getvar('bot_config.boss.boss_name')),
            attacks=self._combo.get_attacks() or None,
            bindings=self._populate_bindings(bindings),
            battle_hp_threshold=var_or_none(self.getvar('bot_config.boss.battle_hp_low')),
            battle_mana_threshold=var_or_none(self.getvar('bot_config.boss.battle_mp_low')),
            buffs=self._tank_buffs.get_attacks() or None,
            buff_interval_secs=var_or_none(self.getvar('bot_config.boss.buff_interval'), float),
            heal_interval_secs=var_or_none(self.getvar('bot_config.boss.heal_interval'), float),
        )

    def _clear(self) -> None:
        self._combo.set_attacks([])
        self._tank_buffs.set_attacks([])
        self._role_var.set("Tank")
        self._on_role_change()
