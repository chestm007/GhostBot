import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.config import Config
from GhostBot.UX import theme as T


class FunctionsFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.config(bg=T.BG_MAIN, width=650, height=459)

        self._vars = dict(
            attack_enabled=tk.BooleanVar(master=self, name="bot_config.attack.enabled", value=False),
            fairy_enabled=tk.BooleanVar(master=self, name="bot_config.fairy.enabled", value=False),
            boss_enabled=tk.BooleanVar(master=self, name="bot_config.boss.enabled", value=False),
            pet_enabled=tk.BooleanVar(master=self, name="bot_config.pet.enabled", value=False),
            sell_enabled=tk.BooleanVar(master=self, name="bot_config.sell.enabled", value=False),

            name=tk.StringVar(master=self, name="char_info.name", value="loading."),
            lvl=tk.StringVar(master=self, name="char_info.level", value="loading."),
            location_name=tk.StringVar(master=self, name="char_info.location_name", value="loading."),
            hp=tk.StringVar(master=self, name="char_info.hp", value="loading."),
            mana=tk.StringVar(master=self, name="char_info.mana", value="loading."),
            target_name=tk.StringVar(master=self, name="char_info.target_name", value="loading."),
            target_hp=tk.StringVar(master=self, name="char_info.target_hp", value="loading."),
            pos=tk.StringVar(master=self, name="char_info.position", value="loading."),
            status=tk.StringVar(master=self, name="char_info.status", value="loading."),
            kills=tk.StringVar(master=self, name="char_info.kills", value="0"),
            farm_time=tk.StringVar(master=self, name="char_info.farm_time", value="00:00:00"),
            energy=tk.StringVar(master=self, name="char_info.energy", value="—"),
            xp=tk.StringVar(master=self, name="char_info.xp", value="+0"),
            gold_g=tk.StringVar(master=self, name="char_info.gold_g", value="0"),
            gold_s=tk.StringVar(master=self, name="char_info.gold_s", value="0"),
            gold_c=tk.StringVar(master=self, name="char_info.gold_c", value="0"),
            current_action=tk.StringVar(master=self, name="char_info.current_action", value="—"),
        )

        # All function checkboxes in a SEPARATE block (top-left), detached from the tall panels' grid
        # -- otherwise Sell/Boss would fall at the same level as the info/action panel.
        checks_frame = tk.Frame(master=self, bg=T.BG_MAIN)
        checks_frame.grid(row=0, column=0, rowspan=8, sticky="nw", padx=4, pady=4)
        _checks = (
            ("Attack", 'attack_enabled'), ("Fairy", 'fairy_enabled'), ("Pet", 'pet_enabled'),
            ("Sell", 'sell_enabled'), ("Boss", 'boss_enabled'),
        )
        self._other_checks = []   # (var_key, checkbutton) for NON-boss functions
        for _i, (_txt, _key) in enumerate(_checks):
            _cb = ttk.Checkbutton(master=checks_frame, text=_txt, style="TCheckbutton", width=13,
                                  variable=self._vars[_key])
            _cb.grid(row=_i, column=0, sticky="w", pady=1)
            if _key != 'boss_enabled':
                self._other_checks.append((_key, _cb))
        # "Boss is Boss-only" rule: turning Boss on unchecks and DISABLES the rest (the boss mode
        # doesn't run alongside normal farming). The trace catches both user clicks and
        # config load (when main.py sets bot_config.boss.enabled).
        self._vars['boss_enabled'].trace_add('write', lambda *a: self._sync_boss_only())

        char_info_frame = tk.Frame(master=self)
        char_info_frame.grid(row=0, column=1, rowspan=5)

        ttk.Label(master=char_info_frame, text="Name:", width=15).grid(row=0, column=0)
        ttk.Label(master=char_info_frame, text="level:", width=15).grid(row=1, column=0)
        ttk.Label(master=char_info_frame, text="Location:", width=15).grid(row=2, column=0)
        ttk.Label(master=char_info_frame, text="HP:", width=15).grid(row=3, column=0)
        ttk.Label(master=char_info_frame, text="Mana:", width=15).grid(row=4, column=0)
        ttk.Label(master=char_info_frame, text="Target Name:", width=15).grid(row=5, column=0)
        ttk.Label(master=char_info_frame, text="Target HP:", width=15).grid(row=6, column=0)
        ttk.Label(master=char_info_frame, text="Pos:", width=15).grid(row=7, column=0)

        ttk.Label(master=char_info_frame, textvariable=self._vars['name'], width=25).grid(row=0, column=1)
        ttk.Label(master=char_info_frame, textvariable=self._vars['lvl'], width=25).grid(row=1, column=1)
        ttk.Label(master=char_info_frame, textvariable=self._vars['location_name'], width=25).grid(row=2, column=1)
        ttk.Label(master=char_info_frame, textvariable=self._vars['hp'], width=25).grid(row=3, column=1)
        ttk.Label(master=char_info_frame, textvariable=self._vars['mana'], width=25).grid(row=4, column=1)
        ttk.Label(master=char_info_frame, textvariable=self._vars['target_name'], width=25).grid(row=5, column=1)
        # Target HP: number + red progress bar
        target_hp_box = tk.Frame(master=char_info_frame)
        target_hp_box.grid(row=6, column=1, sticky="w")
        ttk.Label(master=target_hp_box, textvariable=self._vars['target_hp'], width=5).pack(side="left")
        # Custom style red bar
        style = ttk.Style()
        style.configure("TargetHP.Horizontal.TProgressbar", troughcolor=T.BG_INPUT, background=T.RED, thickness=14)
        self.target_hp_bar = ttk.Progressbar(master=target_hp_box, maximum=100, length=180, style="TargetHP.Horizontal.TProgressbar")
        self.target_hp_bar.pack(side="left", padx=4)

        ttk.Label(master=char_info_frame, textvariable=self._vars['pos'], width=25).grid(row=7, column=1)

        ttk.Label(master=char_info_frame, text="Status:", width=10).grid(row=0, column=2)
        ttk.Label(master=char_info_frame, textvariable=self._vars['status'], width=10).grid(row=0, column=3)

        # Battle indicator (updated externally via main.py)
        ttk.Label(master=char_info_frame, text="Battle:", width=10).grid(row=1, column=2)
        self.battle_label = tk.Label(master=char_info_frame, text="○ Calm", bg=T.BG_PANEL, fg=T.FG_MUTED, width=16, anchor="center")
        self.battle_label.grid(row=1, column=3)

        # Session stats (Kills + Farm time)
        stats_frame = tk.Frame(master=self, bd=1, relief="solid", bg=T.BG_PANEL)
        stats_frame.grid(row=5, column=1, columnspan=3, sticky="ew", padx=8, pady=(12, 4))
        ttk.Label(master=stats_frame, text="📊 CURRENT SESSION", background=T.BG_PANEL, foreground=T.FG_MUTED,
                  font=("TkDefaultFont", 11, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=8, pady=(6, 2))

        ttk.Label(master=stats_frame, text="Mobs killed:", background=T.BG_PANEL,
                  font=("TkDefaultFont", 12)).grid(row=1, column=0, sticky="w", padx=(8, 4), pady=4)
        ttk.Label(master=stats_frame, textvariable=self._vars['kills'], background=T.BG_PANEL,
                  font=("TkDefaultFont", 16, "bold"), foreground=T.GREEN_HI).grid(row=1, column=1, sticky="w", padx=(0, 16), pady=4)

        ttk.Label(master=stats_frame, text="Farm time:", background=T.BG_PANEL,
                  font=("TkDefaultFont", 12)).grid(row=1, column=2, sticky="w", padx=(8, 4), pady=4)
        ttk.Label(master=stats_frame, textvariable=self._vars['farm_time'], background=T.BG_PANEL,
                  font=("TkDefaultFont", 16, "bold"), foreground=T.GREEN_HI).grid(row=1, column=3, sticky="w", padx=(0, 8), pady=4)

        ttk.Label(master=stats_frame, text="Energy:", background=T.BG_PANEL,
                  font=("TkDefaultFont", 12)).grid(row=2, column=0, sticky="w", padx=(8, 4), pady=(0, 6))
        ttk.Label(master=stats_frame, textvariable=self._vars['energy'], background=T.BG_PANEL,
                  font=("TkDefaultFont", 16, "bold"), foreground=T.GREEN_HI).grid(row=2, column=1, sticky="w", padx=(0, 16), pady=(0, 6))

        ttk.Label(master=stats_frame, text="XP gained:", background=T.BG_PANEL,
                  font=("TkDefaultFont", 12)).grid(row=2, column=2, sticky="w", padx=(8, 4), pady=(0, 6))
        ttk.Label(master=stats_frame, textvariable=self._vars['xp'], background=T.BG_PANEL,
                  font=("TkDefaultFont", 16, "bold"), foreground=T.GREEN_HI).grid(row=2, column=3, sticky="w", pady=(0, 6))

        ttk.Label(master=stats_frame, text="Gold gained:", background=T.BG_PANEL,
                  font=("TkDefaultFont", 12)).grid(row=3, column=0, sticky="w", padx=(8, 4), pady=(0, 8))
        _coins = tk.Frame(stats_frame, bg=T.BG_PANEL)
        _coins.grid(row=3, column=1, columnspan=3, sticky="w", pady=(0, 8))
        for _var, _lbl, _color in (('gold_g', 'G', '#c8a227'), ('gold_s', 'S', '#8a8f98'), ('gold_c', 'C', '#b87333')):
            tk.Label(_coins, textvariable=self._vars[_var], bg=T.BG_PANEL, fg=_color,
                     font=("TkDefaultFont", 16, "bold")).pack(side="left")
            tk.Label(_coins, text=_lbl, bg=T.BG_PANEL, fg=_color,
                     font=("TkDefaultFont", 11, "bold")).pack(side="left", padx=(1, 12))

        # BOLDED bar showing the bot's CURRENT ACTION (green, highlighted)
        self.action_label = tk.Label(
            master=self, textvariable=self._vars['current_action'],
            bg=T.GREEN, fg="#0E1714", font=("TkDefaultFont", 13, "bold"),
            anchor="w", padx=10, pady=5)
        self.action_label.grid(row=6, column=0, columnspan=4, sticky="ew", padx=8, pady=(8, 2))

        # SESSION DROPS panel (1-click triage: Want / Don't want)
        drops_frame = tk.Frame(master=self, bd=1, relief="solid", bg=T.BG_PANEL)
        drops_frame.grid(row=7, column=1, columnspan=3, sticky="ew", padx=8, pady=(4, 8))
        ttk.Label(master=drops_frame, text="🎁 SESSION DROPS", background=T.BG_PANEL,
                  foreground=T.FG_MUTED, font=("TkDefaultFont", 11, "bold")).pack(
            anchor="w", padx=8, pady=(6, 2))
        self.drops_container = tk.Frame(master=drops_frame, bg=T.BG_PANEL)
        self.drops_container.pack(fill="x", padx=4, pady=(0, 6))
        self._last_drops = None
        self._config_frames: dict[str, TabFrame] = {}
        self.update_drops({})  # initial placeholder

    def _sync_boss_only(self):
        """'Boss is Boss-only' rule: with Boss on, unchecks and DISABLES the other
        functions (can't check them). Boss off -> re-enables. Called by the trace of
        bot_config.boss.enabled (user click or config load)."""
        boss_on = bool(self._vars['boss_enabled'].get())
        for _key, _cb in getattr(self, '_other_checks', []):
            if boss_on:
                self._vars[_key].set(False)
                _cb.state(['disabled'])
            else:
                _cb.state(['!disabled'])

    def update_drops(self, drops: dict):
        """Thread-safe entry (called by IPC thread): only redraws when
        drops change, and schedules the draw on the UI thread (tkinter is not thread-safe)."""
        drops = drops or {}
        if drops == self._last_drops:
            return
        self._last_drops = dict(drops)
        self.after(0, lambda d=dict(drops): self._render_drops(d))

    def _render_drops(self, drops: dict):
        """Redraws the drops list. Already-classified item shows a TAG
        (🎯 want / 🚫 ignored); undecided item shows the buttons."""
        for w in self.drops_container.winfo_children():
            w.destroy()
        if not drops:
            tk.Label(self.drops_container, text="(no drops yet)", bg=T.BG_PANEL,
                     fg=T.FG_MUTED, font=("TkDefaultFont", 11)).pack(anchor="w", padx=8)
            return
        try:
            from GhostBot.drop_watcher import load_watchlist, default_watchlist_path
            want, ignore = load_watchlist(default_watchlist_path())
        except Exception:
            want, ignore = set(), set()
        for name, count in sorted(drops.items(), key=lambda kv: -kv[1]):
            low = name.lower()
            row = tk.Frame(self.drops_container, bg=T.BG_PANEL)
            row.pack(fill="x", padx=4, pady=1)
            tk.Label(row, text=f"{name}  ×{count}", bg=T.BG_PANEL, fg=T.FG_MAIN,
                     font=("TkDefaultFont", 11), anchor="w", width=30).pack(side="left")
            if low in want:
                tk.Label(row, text="🎯 want", bg=T.BG_PANEL, fg=T.GREEN_HI,
                         font=("TkDefaultFont", 10, "bold")).pack(side="left", padx=4)
            elif low in ignore:
                tk.Label(row, text="🚫 ignored", bg=T.BG_PANEL, fg=T.FG_MUTED,
                         font=("TkDefaultFont", 10)).pack(side="left", padx=4)
            else:
                tk.Button(row, text="✅ Want", bg=T.BG_PANEL, fg=T.GREEN_HI, bd=1,
                          activebackground="#26392F", relief="solid",
                          command=lambda n=name: self._triage(n, "want")).pack(side="left", padx=2)
                tk.Button(row, text="❌ Don't", bg=T.BG_PANEL, fg=T.RED, bd=1,
                          activebackground="#3a2222", relief="solid",
                          command=lambda n=name: self._triage(n, "ignore")).pack(side="left", padx=2)

    def _triage(self, name: str, which: str):
        """Dashboard button: puts the item in the WANT or DON'T WANT list (writes
        to alertas_drop.txt; the server's DropWatch reloads automatically). Redraws
        immediately, so that item's buttons turn into tags instantly."""
        try:
            from GhostBot.drop_watcher import add_to_watchlist
            add_to_watchlist(name, which)
        except Exception:
            pass
        self._render_drops(self._last_drops or {})

    def register_config_frames(self, **frames):
        self._config_frames = {k: v for k, v in frames.items() if v is not None}

    def save_config(self):
        def _function_enabled(f):
            return int(self.getvar(f'bot_config.{f}.enabled')) == 1

        _config = Config()

        for key, frame in self._config_frames.items():
            if _function_enabled(key):
                setattr(_config, key, frame.extract_config())
        return _config
