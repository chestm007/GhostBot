import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.attack_frame import AttackFrame
from GhostBot.UX.tabbed_widget.buff_frame import BuffFrame
from GhostBot.UX.tabbed_widget.delete_frame import DeleteFrame
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
            delete_enabled=tk.BooleanVar(master=self, name="bot_config.delete.enabled", value=False),

            name=tk.StringVar(master=self, name="char_info.name", value="loading."),
            lvl=tk.StringVar(master=self, name="char_info.level", value="loading."),
            location_name=tk.StringVar(master=self, name="char_info.location_name", value="loading."),
            hp=tk.StringVar(master=self, name="char_info.hp", value="loading."),
            mana=tk.StringVar(master=self, name="char_info.mana", value="loading."),
            target_name=tk.StringVar(master=self, name="char_info.target_name", value="loading."),
            target_hp=tk.StringVar(master=self, name="char_info.target_hp", value="loading."),
            pos=tk.StringVar(master=self, name="char_info.position", value="loading."),
            status=tk.StringVar(master=self, name="char_info.status", value="loading."),
        )

        ttk.Checkbutton(master=self, text="Attack", style="TCheckbutton", width=13, variable=self._vars['attack_enabled']).grid(row=0, column=0)
        ttk.Checkbutton(master=self, text="Fairy", style="TCheckbutton", width=13, variable=self._vars['fairy_enabled']).grid(row=1, column=0)
        ttk.Checkbutton(master=self, text="Buff", style="TCheckbutton", width=13, variable=self._vars['buff_enabled']).grid(row=2, column=0)
        ttk.Checkbutton(master=self, text="Regen", style="TCheckbutton", width=13, variable=self._vars['regen_enabled']).grid(row=3, column=0)
        ttk.Checkbutton(master=self, text="Pet", style="TCheckbutton", width=13, variable=self._vars['pet_enabled']).grid(row=4, column=0)
        ttk.Checkbutton(master=self, text="Sell", style="TCheckbutton", width=13, variable=self._vars['sell_enabled']).grid(row=5, column=0)
        ttk.Checkbutton(master=self, text="Delete", style="TCheckbutton", width=13, variable=self._vars['delete_enabled']).grid(row=6, column=0)

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
        ttk.Label(master=char_info_frame, textvariable=self._vars['target_hp'], width=25).grid(row=6, column=1)
        ttk.Label(master=char_info_frame, textvariable=self._vars['pos'], width=25).grid(row=7, column=1)

        ttk.Label(master=char_info_frame, text="Status:", width=10).grid(row=0, column=2)
        ttk.Label(master=char_info_frame, textvariable=self._vars['status'], width=10).grid(row=0, column=3)

    def save_config(self):
        _config = Config()

        for child in (c for c in self.master.children.values() if isinstance(c, tk.Frame)):
            if isinstance(child, AttackFrame) and self.getvar('bot_config.attack.enabled'):
                _config.attack = child.extract_config()
            elif isinstance(child, BuffFrame) and self.getvar('bot_config.buff.enabled'):
                _config.buff = child.extract_config()
            elif isinstance(child, RegenFrame) and self.getvar('bot_config.regen.enabled'):
                _config.regen = child.extract_config()
            elif isinstance(child, PetFrame) and self.getvar('bot_config.pet.enabled'):
                _config.pet = child.extract_config()
            elif isinstance(child, FairyFrame) and self.getvar('bot_config.fairy.enabled'):
                _config.fairy = child.extract_config()
            elif isinstance(child, SellFrame) and self.getvar('bot_config.sell.enabled'):
                _config.sell = child.extract_config()
            elif isinstance(child, DeleteFrame) and self.getvar('bot_config.delete.enabled'):
                _config.delete = child.extract_config()
        return _config
