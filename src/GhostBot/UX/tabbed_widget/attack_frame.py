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
        # Classe (dropdown): muda os EXTRAS por classe no farm. DPS (padrao) = comportamento atual.
        ttk.Label(self, text="Classe:", anchor="w").grid(row=0, column=0, padx=4, pady=(6, 2), sticky="w")
        self._class_var = tk.StringVar(master=self, name="bot_config.attack.char_class_label", value="DPS")
        self._class_combo = ttk.Combobox(self, textvariable=self._class_var, values=["DPS", "Tamer", "Fairy"],
                                          state="readonly", width=10)
        self._class_combo.grid(row=0, column=1, padx=2, pady=(6, 2), sticky="w")
        self._class_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_class_change())

        # Faixa HP — Frame inteiro colorido, widgets dentro
        hp_row = tk.Frame(self, bg=HP_BG)
        hp_row.grid(row=1, column=0, columnspan=12, sticky="ew", padx=2, pady=1)

        # Faixa MP
        mp_row = tk.Frame(self, bg=MP_BG)
        mp_row.grid(row=2, column=0, columnspan=12, sticky="ew", padx=2, pady=1)

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
                self, "Sem dano por (s):", 3, 0, "bot_config.attack.battle_stuck",
                default=8, min_val=1, max_val=10, suffix="s",
                hint="Se o HP do alvo não cair por esse tempo, o bot considera travado e troca de alvo",
            ),
            roam=create_int_slider(
                self, "Distância máx do spot:", 4, 0, "bot_config.attack.battle_roam",
                default=40, min_val=15, max_val=100, suffix="un",
                hint="Raio de farm ao redor do Spot. Se o personagem passar dessa distância, ele "
                     "recentraliza no Spot (pequenos cliques no minimapa). 15=bem grudado · 100=mais solto.",
            ),
            spot=create_entry(
                self, "Spot (X,Y):", 6, 0, ("bot_config.attack.spot", str),
                hint="Coordenadas X,Y do ponto de farm — medem a distância pra saber quando voltar. "
                     "Preenchido por 'Posição atual' ou pelo '📍 Capturar spot' abaixo.",
            ),
            map_spot=create_entry(
                self, "Spot de farm (mapa):", 7, 0, ("bot_config.attack.return_spot_map_offset", str),
                hint="Pra ONDE o bot volta quando sai do raio de farm (clique no MAPA aberto). Fique no "
                     "spot, abra o MAPA (M), ponha o mouse no seu personagem no mapa e clique "
                     "'📍 Capturar spot'. É o MESMO da aba Sell (sincronizado: mexe num, muda no outro).",
            ),
            boss_lock=create_entry(
                self, "Travar no Boss", 8, 0, ("bot_config.attack.boss_lock", bool),
                hint="Se marcado, o bot dá TAB até achar o NOME do boss (abaixo) e ataca SÓ ele "
                     "(ignora mobs comuns). Pra boss runs.",
            ),
            boss_name=create_entry(
                self, "Nome do Boss:", 9, 0, ("bot_config.attack.boss_name", str), entry_width=18,
                hint="Nome (ou parte) do boss pra travar o alvo. Ex.: 'Jing Gou'. Só vale com "
                     "'Travar no Boss' marcado.",
            ),
        )

        # Combo dinâmico: 1 linha vazia inicialmente, usuário adiciona/remove
        self._combo = ComboWidget(
            self, "Combo:", grid_row=5, grid_column=0,
            hint="Sequência de teclas que o bot aperta em loop. Cada linha: tecla + intervalo em milissegundos. Adicione quantas quiser.",
        )
        self._combo.add_row()  # 1 linha vazia pra começar

        ttk.Button(
            master=self, text="Posição atual", command=lambda: self._set_spot_as_current('spot')
        ).grid(row=6, column=2, padx=4)

        ttk.Button(
            master=self, text="📍 Capturar spot", command=self._capture_farm_spot
        ).grid(row=7, column=2, padx=4)

        ttk.Button(
            master=self, text="🎯 Pegar alvo", command=self._grab_target_name
        ).grid(row=9, column=2, padx=4)

        # ---- Extras por CLASSE (aparecem conforme o dropdown) ----
        # Tamer: tecla de ataque do pet. Fairy: tecla de cura (usada no lugar do pot HP).
        self._tamer_extra = tk.Frame(self, bg=T.BG_MAIN)
        self._tamer_extra.grid(row=10, column=0, columnspan=12, sticky="w")
        self._vars['pet_attack'] = create_entry(
            self._tamer_extra, "Tecla ataque do pet:", 0, 0, ("bot_config.attack.pet_attack", str), entry_width=3,
            hint="Tamer: tecla que manda o pet atacar. O bot aperta ao pegar CADA novo alvo.",
        )
        self._fairy_extra = tk.Frame(self, bg=T.BG_MAIN)
        self._fairy_extra.grid(row=10, column=0, columnspan=12, sticky="w")
        self._vars['heal'] = create_entry(
            self._fairy_extra, "Tecla de Cura:", 0, 0, ("bot_config.attack.heal", str), entry_width=3,
            hint="Fairy: ao cair do 'Pot HP em %', ela aperta ESTA cura (em vez de pot de vida). MP segue por pot.",
        )
        self._on_class_change()

    def _on_class_change(self) -> None:
        """Mostra os extras da classe escolhida (Tamer = tecla do pet; Fairy = tecla de cura)."""
        cls = self._class_var.get()
        self._tamer_extra.grid_remove()
        self._fairy_extra.grid_remove()
        if cls == "Tamer":
            self._tamer_extra.grid()
        elif cls == "Fairy":
            self._fairy_extra.grid()

    def _set_spot_as_current(self, field: str):
        self._vars[field].set(eval(self.master.getvar('char_info.position')))

    def _grab_target_name(self):
        """Pega o nome do alvo SELECIONADO no jogo e poe no campo 'Nome do Boss'
        (evita erro de digitacao). Reusa o que o servidor ja manda em char_info.target_name.
        Sem alvo valido -> avisa no proprio campo em vez de colar lixo."""
        name = (self.master.getvar('char_info.target_name') or '').strip()
        if name.lower() in ('', 'none', 'loading.', 'loading'):
            self._vars['boss_name'].set("(selecione um alvo no jogo)")
            return
        self._vars['boss_name'].set(name)

    def _capture_farm_spot(self):
        """Captura o spot de farm de uma vez: a posicao X,Y do char (mede distancia)
        E o offset do MAPA (pro retorno por mapa, sincronizado com a aba Sell).
        Fique no spot, abra o MAPA (M), ponha o mouse no seu personagem no mapa, clique."""
        import time
        import ctypes
        from ctypes import wintypes
        import win32api
        from GhostBot.lib.win32.process import PymemProcess
        from GhostBot.client_window import Win32ClientWindow

        # 1) X,Y atual do char (pra medir a distancia ao spot)
        try:
            self._set_spot_as_current('spot')
        except Exception:
            pass
        # 2) offset do mapa (pro clique de retorno) -- mesma logica da aba Sell
        var = self._vars['map_spot']
        var.set("Abra o mapa (M) e ponha o mouse no spot...")
        self.update_idletasks()
        time.sleep(4)
        try:
            proc = next(iter(PymemProcess.list_clients()), None)
            if proc is None:
                var.set("(client.exe nao encontrado)")
                return
            client = Win32ClientWindow(proc)
            title = client._image_finder.find_button_center('map_title.bmp', threshold=0.70)
            if title is None:
                var.set("(titulo 'Map' nao achado - mapa aberto/visivel?)")
                return
            sx, sy = win32api.GetCursorPos()
            pt = wintypes.POINT(sx, sy)
            ctypes.windll.user32.ScreenToClient(client.window_handle, ctypes.byref(pt))
            var.set("{} {}".format(pt.x - title[0], pt.y - title[1]))
        except Exception as e:
            var.set(f"(erro: {e})")

    def display_config(self, config: Config):
        if config.attack:
            hp_key = mp_key = pet_key = heal_key = ''
            if config.attack.bindings:
                _b = config.attack.bindings
                hp_key = str(_b.get('battle_hp_pot', '') or '')
                mp_key = str(_b.get('battle_mana_pot', '') or '')
                pet_key = str(_b.get('pet_attack', '') or '')
                heal_key = str(_b.get('heal', '') or '')
            self.setvar('bot_config.attack.battle_hp_key', hp_key)
            self.setvar('bot_config.attack.battle_mp_key', mp_key)
            self.setvar('bot_config.attack.pet_attack', pet_key)
            self.setvar('bot_config.attack.heal', heal_key)
            self._class_var.set(
                {'dps': 'DPS', 'tamer': 'Tamer', 'fairy': 'Fairy'}.get(
                    (config.attack.char_class or 'dps').lower(), 'DPS'))
            self._on_class_change()

            self.setvar('bot_config.attack.battle_hp_low', str(config.attack.battle_hp_threshold or ''))
            self.setvar('bot_config.attack.battle_mp_low', str(config.attack.battle_mana_threshold or ''))
            self.setvar('bot_config.attack.battle_stuck', str(config.attack.stuck_interval or ''))
            self.setvar('bot_config.attack.battle_roam', str(config.attack.roam_distance or ''))
            self.setvar('bot_config.attack.spot', _format_spot(config.attack.spot))
            self.setvar('bot_config.attack.return_spot_map_offset',
                        _format_spot(config.attack.return_spot_map_offset))
            self.setvar('bot_config.attack.boss_lock', bool(config.attack.boss_lock))
            self.setvar('bot_config.attack.boss_name', config.attack.boss_name or '')

            self._combo.set_attacks(config.attack.attacks or [])
        else:
            self.clear()

    def extract_config(self) -> AttackConfig:
        bindings = dict(
            battle_hp_pot=self._nullable_string(self.getvar('bot_config.attack.battle_hp_key')),
            battle_mana_pot=self._nullable_string(self.getvar('bot_config.attack.battle_mp_key')),
            pet_attack=self._nullable_string(self.getvar('bot_config.attack.pet_attack')),
            heal=self._nullable_string(self.getvar('bot_config.attack.heal')),
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
            return_spot_map_offset=var_or_none(self.getvar('bot_config.attack.return_spot_map_offset')),
            boss_lock=var_or_none(self.getvar('bot_config.attack.boss_lock')),
            boss_name=var_or_none(self.getvar('bot_config.attack.boss_name')),
            char_class=(self._class_var.get() or 'DPS').lower(),
        )

    def _clear(self):
        self._combo.set_attacks([])
