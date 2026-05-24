import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.attack_frame import AttackFrame
from GhostBot.UX.tabbed_widget.buff_frame import BuffFrame
from GhostBot.UX.tabbed_widget.fairy_frame import FairyFrame
from GhostBot.UX.tabbed_widget.pet_frame import PetFrame
from GhostBot.UX.tabbed_widget.regen_frame import RegenFrame
from GhostBot.UX.tabbed_widget.sell_frame import SellFrame
from GhostBot.config import Config


class FunctionsFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.config(bg="#EDECEC", width=650, height=459)

        self._vars = dict(
            attack_enabled=tk.BooleanVar(master=self, name="bot_config.attack.enabled", value=False),
            fairy_enabled=tk.BooleanVar(master=self, name="bot_config.fairy.enabled", value=False),
            buff_enabled=tk.BooleanVar(master=self, name="bot_config.buff.enabled", value=False),
            regen_enabled=tk.BooleanVar(master=self, name="bot_config.regen.enabled", value=False),
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
        )

        ttk.Checkbutton(master=self, text="Attack", style="TCheckbutton", width=13, variable=self._vars['attack_enabled']).grid(row=0, column=0)
        ttk.Checkbutton(master=self, text="Fairy", style="TCheckbutton", width=13, variable=self._vars['fairy_enabled']).grid(row=1, column=0)
        ttk.Checkbutton(master=self, text="Buff", style="TCheckbutton", width=13, variable=self._vars['buff_enabled']).grid(row=2, column=0)
        ttk.Checkbutton(master=self, text="Regen", style="TCheckbutton", width=13, variable=self._vars['regen_enabled']).grid(row=3, column=0)
        ttk.Checkbutton(master=self, text="Pet", style="TCheckbutton", width=13, variable=self._vars['pet_enabled']).grid(row=4, column=0)
        ttk.Checkbutton(master=self, text="Sell", style="TCheckbutton", width=13, variable=self._vars['sell_enabled']).grid(row=5, column=0)

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
        # Target HP: numero + barra de progresso vermelha
        target_hp_box = tk.Frame(master=char_info_frame)
        target_hp_box.grid(row=6, column=1, sticky="w")
        ttk.Label(master=target_hp_box, textvariable=self._vars['target_hp'], width=5).pack(side="left")
        # Custom style red bar
        style = ttk.Style()
        style.configure("TargetHP.Horizontal.TProgressbar", troughcolor="#444", background="#e04040", thickness=14)
        self.target_hp_bar = ttk.Progressbar(master=target_hp_box, maximum=100, length=180, style="TargetHP.Horizontal.TProgressbar")
        self.target_hp_bar.pack(side="left", padx=4)

        ttk.Label(master=char_info_frame, textvariable=self._vars['pos'], width=25).grid(row=7, column=1)

        ttk.Label(master=char_info_frame, text="Status:", width=10).grid(row=0, column=2)
        ttk.Label(master=char_info_frame, textvariable=self._vars['status'], width=10).grid(row=0, column=3)

        # Indicador de combate (atualizado externamente via main.py)
        ttk.Label(master=char_info_frame, text="Combate:", width=10).grid(row=1, column=2)
        self.battle_label = tk.Label(master=char_info_frame, text="○ Tranquilo", bg="#dddddd", fg="#222", width=16, anchor="center")
        self.battle_label.grid(row=1, column=3)

        # Stats da sessao (Kills + Tempo de farm)
        stats_frame = tk.Frame(master=self, bd=1, relief="solid", bg="#ffffff")
        stats_frame.grid(row=5, column=1, columnspan=3, sticky="ew", padx=8, pady=(12, 4))
        ttk.Label(master=stats_frame, text="📊 SESSÃO ATUAL", background="#ffffff", foreground="#666",
                  font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=8, pady=(6, 2))

        ttk.Label(master=stats_frame, text="Mobs mortos:", background="#ffffff",
                  font=("TkDefaultFont", 10)).grid(row=1, column=0, sticky="w", padx=(8, 4), pady=4)
        ttk.Label(master=stats_frame, textvariable=self._vars['kills'], background="#ffffff",
                  font=("TkDefaultFont", 14, "bold"), foreground="#1f6feb").grid(row=1, column=1, sticky="w", padx=(0, 16), pady=4)

        ttk.Label(master=stats_frame, text="Tempo de farm:", background="#ffffff",
                  font=("TkDefaultFont", 10)).grid(row=1, column=2, sticky="w", padx=(8, 4), pady=4)
        ttk.Label(master=stats_frame, textvariable=self._vars['farm_time'], background="#ffffff",
                  font=("TkDefaultFont", 14, "bold"), foreground="#1f6feb").grid(row=1, column=3, sticky="w", padx=(0, 8), pady=4)

        ttk.Label(master=stats_frame, text="Energy:", background="#ffffff",
                  font=("TkDefaultFont", 10)).grid(row=2, column=0, sticky="w", padx=(8, 4), pady=(0, 6))
        ttk.Label(master=stats_frame, textvariable=self._vars['energy'], background="#ffffff",
                  font=("TkDefaultFont", 14, "bold"), foreground="#1f6feb").grid(row=2, column=1, sticky="w", padx=(0, 16), pady=(0, 6))

        ttk.Label(master=stats_frame, text="XP ganho:", background="#ffffff",
                  font=("TkDefaultFont", 10)).grid(row=2, column=2, sticky="w", padx=(8, 4), pady=(0, 6))
        ttk.Label(master=stats_frame, textvariable=self._vars['xp'], background="#ffffff",
                  font=("TkDefaultFont", 14, "bold"), foreground="#1f6feb").grid(row=2, column=3, sticky="w", pady=(0, 6))

        ttk.Label(master=stats_frame, text="Gold ganho:", background="#ffffff",
                  font=("TkDefaultFont", 10)).grid(row=3, column=0, sticky="w", padx=(8, 4), pady=(0, 8))
        _coins = tk.Frame(stats_frame, bg="#ffffff")
        _coins.grid(row=3, column=1, columnspan=3, sticky="w", pady=(0, 8))
        for _var, _lbl, _color in (('gold_g', 'G', '#c8a227'), ('gold_s', 'S', '#8a8f98'), ('gold_c', 'C', '#b87333')):
            tk.Label(_coins, textvariable=self._vars[_var], bg="#ffffff", fg=_color,
                     font=("TkDefaultFont", 14, "bold")).pack(side="left")
            tk.Label(_coins, text=_lbl, bg="#ffffff", fg=_color,
                     font=("TkDefaultFont", 9, "bold")).pack(side="left", padx=(1, 12))

    def save_config(self):
        def _function_enabled(f):
            return int(self.getvar(f'bot_config.{f}.enabled')) == 1
        
        _config = Config()

        for child in (c for c in self.master.children.values() if isinstance(c, tk.Frame)):
            if isinstance(child, AttackFrame) and _function_enabled('attack'):
                _config.attack = child.extract_config()
            elif isinstance(child, BuffFrame) and _function_enabled('buff'):
                _config.buff = child.extract_config()
            elif isinstance(child, RegenFrame) and _function_enabled('regen'):
                _config.regen = child.extract_config()
            elif isinstance(child, PetFrame) and _function_enabled('pet'):
                _config.pet = child.extract_config()
            elif isinstance(child, FairyFrame) and _function_enabled('fairy'):
                _config.fairy = child.extract_config()
            elif isinstance(child, SellFrame) and _function_enabled('sell'):
                _config.sell = child.extract_config()
        return _config
