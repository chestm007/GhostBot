import contextlib
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog

from GhostBot import logger
from GhostBot.UX.autologin.main import GhostBotAutoLogin
from GhostBot.UX.tabbed_widget.sell_frame import SellFrame
from GhostBot.config import Config
from GhostBot.IPC.message import Command
from GhostBot.server import GhostbotIPCClient

from GhostBot.UX.pyuiWidgets.logWindow import LogWindow
from GhostBot.UX.pyuiWidgets.listBox import ScrollableListbox
from GhostBot.UX.pyuiWidgets.tabbedWidget import TabbedWidget

from GhostBot.UX.tabbed_widget.attack_frame import AttackFrame
from GhostBot.UX.tabbed_widget.buff_frame import BuffFrame
from GhostBot.UX.tabbed_widget.fairy_frame import FairyFrame
from GhostBot.UX.tabbed_widget.functions import FunctionsFrame
from GhostBot.UX.tabbed_widget.pet_frame import PetFrame
from GhostBot.UX.tabbed_widget.regen_frame import RegenFrame


class GhostBot(tk.Tk):
    def __init__(self):
        super().__init__()
        self.client = GhostbotIPCClient()
        self.title("GhostBot")

        # Paleta moderna clean
        BG_MAIN = "#eef1f5"     # bg da janela
        BG_PANEL = "#ffffff"    # bg dos paineis (tabs)
        BG_LIST = "#3a3f4b"     # bg da lista de chars (escuro pra contraste)
        FG_LIST = "#e8eaed"
        ACCENT = "#4a90e2"

        self.config(bg=BG_MAIN)
        self.geometry("980x680")
        self.minsize(820, 560)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Fonte global maior
        _default_font = ("TkDefaultFont", 10)
        self.style.configure(".", font=_default_font, background=BG_MAIN)
        self.option_add("*Font", "TkDefaultFont 10")

        # Estilos botoes / labels
        self.style.configure("TButton", padding=6, relief="solid", borderwidth=1,
                             bordercolor=ACCENT, background="#dfe4eb", foreground="#1f2937")
        self.style.map("TButton", background=[("active", "#c8d1dc")],
                       bordercolor=[("active", "#3a7bc8")])
        self.style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff")
        self.style.map("Accent.TButton", background=[("active", "#3a7bc8")])
        self.style.configure("TLabel", background=BG_MAIN)
        self.style.configure("TFrame", background=BG_MAIN)
        self.style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=(12, 6), background="#cfd6e0", foreground="#1f2937")
        self.style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "#ffffff")])

        self.style.configure("attack.TCheckbutton", background=BG_MAIN, foreground="#1f2937")
        self.style.map("attack.TCheckbutton", background=[("active", "#dfe4eb")], foreground=[("active", "#1f2937")])

        self.menu = GhostBotMenu(self)
        self.config(menu=self.menu)

        # === LAYOUT RESPONSIVO COM GRID ===
        # Coluna 0 (lista): largura fixa.  Coluna 1 (tabs/log): expande.
        # Linha 0 (tabs+log via PanedWindow): expande.  Linha 1 (botoes): altura fixa.
        self.grid_columnconfigure(0, weight=0, minsize=180)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self._char_list = tk.Variable(master=self)
        self.client.add_callback(Command.LOG, lambda message: self.log.insert_log(message.target))
        self.client.add_callback(Command.INFO, lambda message: self.set_char_list(message.target.split(' ')))
        self.client.add_callback(Command.INFO_CHAR, lambda message: update_char_info_display(message.target))

        self.list_box = ScrollableListbox(parent=self, scrollx=False, scrolly=True, listvariable=self._char_list)
        self.list_box.config(bg=BG_LIST, fg=FG_LIST, borderwidth=0, highlightthickness=0,
                             selectbackground=ACCENT, selectforeground="#ffffff")
        self.list_box.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(6, 3), pady=6)

        # PanedWindow vertical: tabs em cima, log embaixo. Usuario arrasta o divisor.
        self._splitter = tk.PanedWindow(self, orient=tk.VERTICAL, sashwidth=6, bg=BG_MAIN,
                                        sashrelief="flat", borderwidth=0)
        self._splitter.grid(row=0, column=1, sticky="nsew", padx=(3, 6), pady=(6, 3))

        self.tabbed_widget = TabbedWidget(self._splitter, enable_reorder=False)
        self.tabbed_widget.config()
        self._splitter.add(self.tabbed_widget, minsize=280, stretch="always")

        self.log = LogWindow(master=self._splitter)
        self.log.configure(bg="#1e1f22", fg="#dcddde", borderwidth=0, highlightthickness=0,
                           insertbackground="#dcddde")
        self._splitter.add(self.log, minsize=80, height=140, stretch="never")

        _functions_frame = FunctionsFrame(master=self.tabbed_widget)
        self._functions_frame = _functions_frame
        self._attack_frame = AttackFrame(master=self.tabbed_widget)
        self._buff_frame = BuffFrame(master=self.tabbed_widget)
        self._fairy_frame = FairyFrame(master=self.tabbed_widget)
        self._pet_frame = PetFrame(master=self.tabbed_widget)
        self._regen_frame = RegenFrame(master=self.tabbed_widget, client=self.client)
        self._sell_frame = SellFrame(master=self.tabbed_widget, client=self.client)

        self.tabbed_widget.add(_functions_frame, text="Dashboard")
        self.tabbed_widget.add(self._attack_frame, text="Attack")
        self.tabbed_widget.add(self._fairy_frame, text="Fairy")
        self.tabbed_widget.add(self._buff_frame, text="Buff")
        self.tabbed_widget.add(self._regen_frame, text="Regen")
        self.tabbed_widget.add(self._pet_frame, text="Pet")
        self.tabbed_widget.add(self._sell_frame, text="Sell")

        def update_char_info_display(response):
            if response.get('name') != self.selected_char():
                return

            self.tabbed_widget.setvar("char_info.name", response.get("name", 'loading.'))
            self.tabbed_widget.setvar("char_info.level", response.get("level", 'loading.'))
            self.tabbed_widget.setvar("char_info.location_name", response.get("location_name", 'loading.'))
            self.tabbed_widget.setvar("char_info.hp", f"{response.get("hp")}/{response.get("max_hp")}")
            self.tabbed_widget.setvar("char_info.mana", f"{response.get("mana")}/{response.get("max_mana")}")
            self.tabbed_widget.setvar("char_info.target_name", response.get("target_name", 'loading.'))
            self.tabbed_widget.setvar("char_info.target_hp", response.get("target_hp", 'loading.'))
            self.tabbed_widget.setvar("char_info.position", f"({response.get("location_x")}, {response.get("location_y")})")
            self.tabbed_widget.setvar("char_info.status", response.get("status", 'loading.'))
            self.tabbed_widget.setvar("window_info.pos", response.get("window_pos", ''))
            self.tabbed_widget.setvar("window_info.size", response.get("window_size", ''))

            # Barra HP do alvo (0-100, -1 = morto/sem alvo)
            t_hp = response.get("target_hp", 0)
            try:
                t_hp_int = int(t_hp) if t_hp is not None else 0
                self._functions_frame.target_hp_bar['value'] = max(0, t_hp_int)
            except (ValueError, TypeError):
                self._functions_frame.target_hp_bar['value'] = 0

            # Indicador de combate
            if response.get("in_battle"):
                self._functions_frame.battle_label.config(text="🔴 EM COMBATE", bg="#e04040", fg="white")
            else:
                self._functions_frame.battle_label.config(text="○ Tranquilo", bg="#dddddd", fg="#222")

            # Stats (Dashboard)
            self.tabbed_widget.setvar("char_info.kills", str(response.get("kills", 0)))
            farm_s = int(response.get("farm_time_s") or 0)
            h, rem = divmod(farm_s, 3600)
            m, s = divmod(rem, 60)
            self.tabbed_widget.setvar("char_info.farm_time", f"{h:02d}:{m:02d}:{s:02d}")
            _energy = response.get("energy")
            self.tabbed_widget.setvar("char_info.energy", str(_energy) if _energy is not None else "—")
            self.tabbed_widget.setvar("char_info.xp", f"+{response.get('xp_gained', 0)}")
            # gold_gained vem em COPPER -> separa em Gold/Silver/Copper (100c=1s, 100s=1g)
            _copper_total = max(0, int(response.get('gold_gained', 0) or 0))
            _g, _rem = divmod(_copper_total, 10000)
            _s, _c = divmod(_rem, 100)
            self.tabbed_widget.setvar("char_info.gold_g", str(_g))
            self.tabbed_widget.setvar("char_info.gold_s", str(_s))
            self.tabbed_widget.setvar("char_info.gold_c", str(_c))

        self.client.add_callback(Command.CONFIG, self._update_char_config)

        def save_config():
            self.client.set_config(
                target=_functions_frame.getvar('char_info.name'),
                config=_functions_frame.save_config()
            )

        # Botoes em frame, alinhados a direita
        _btn_frame = ttk.Frame(self)
        _btn_frame.grid(row=1, column=1, sticky="e", padx=(3, 10), pady=(3, 8))
        ttk.Button(
            master=_btn_frame, text="Start", style="Accent.TButton",
            command=lambda: self.client.start_bot(self.selected_char())
        ).pack(side="left", padx=2)
        ttk.Button(
            master=_btn_frame, text="Stop",
            command=lambda: self.client.stop_bot(self.selected_char())
        ).pack(side="left", padx=2)
        ttk.Button(master=_btn_frame, text="Save", width=10, command=save_config).pack(side="left", padx=2)

        self.client.add_callback(Command.CONFIG_GET, lambda message: self._update_char_config(Config.load_yaml(message.target)))

        self.client.add_callback(
            Command.CONFIG_SET, lambda message: self.log.insert_log(f'Config set for {message.target.get("char")}')
        )

        self.client.run()

    def _update_char_config(self, bot_config: Config):

        self.tabbed_widget.setvar("bot_config.attack.enabled", bool(bot_config.attack))
        self.tabbed_widget.setvar("bot_config.pet.enabled", bool(bot_config.pet))
        self.tabbed_widget.setvar("bot_config.buff.enabled", bool(bot_config.buff))
        self.tabbed_widget.setvar("bot_config.regen.enabled", bool(bot_config.regen))
        self.tabbed_widget.setvar("bot_config.fairy.enabled", bool(bot_config.fairy))
        self.tabbed_widget.setvar('bot_config.sell.enabled', bool(bot_config.sell))

        self._attack_frame.display_config(bot_config)
        self._buff_frame.display_config(bot_config)
        self._fairy_frame.display_config(bot_config)
        self._pet_frame.display_config(bot_config)
        self._regen_frame.display_config(bot_config)
        self._sell_frame.display_config(bot_config)

    def set_char_list(self, _char_list):
        # tk.Variable.get() devolve TUPLA pra lista (ou '' se vazio); _char_list eh LISTA.
        # Comparar tupla com lista dava SEMPRE diferente -> repovoava o listbox a cada poll
        # -> limpava a selecao do usuario -> congelava o dashboard. Normaliza antes de comparar.
        _cur = self._char_list.get()
        _cur = list(_cur) if isinstance(_cur, (tuple, list)) else []
        if _cur != list(_char_list):
            self._char_list.set(_char_list)

    def append_log(self, msg: str):
        self.log.append_log(msg)

    def selected_char(self):
        try:
            if _selection_list := self.list_box.curselection():
                return self.list_box.get(_selection_list[0])
        except tk.TclError:
            return None

class GhostBotMenu (tk.Menu):
    master: GhostBot

    def __init__(self, master: GhostBot):
        super().__init__(master)

        menu_0 = tk.Menu(self, tearoff=0)
        menu_0.add_command(label="Import char config", command=self._import_char_config)
        menu_0.add_command(label="Export char config", command=self._export_char_config)
        menu_0.add_command(label="Shutdown server", command=self.master.client.shutdown_server)
        menu_0.add_command(label="Auto login configuration", command=lambda: GhostBotAutoLogin(self, client=self.master.client))
        menu_0.add_command(label="Exit", command=self.master.destroy)
        self.add_cascade(label="File", menu=menu_0)

        menu_1 = tk.Menu(self, tearoff=0)
        menu_1.add_command(label="About")
        self.add_cascade(label="Help", menu=menu_1)

    def _import_char_config(self):
        _file = self._select_open_file()[0]
        print('importing char config %s', _file)
        char_config = Config.load_file(_file)
        print(char_config)
        if char_config:
            self.master._update_char_config(char_config)
            self.master.log.insert_log(f'Imported char config for {self.master.selected_char()} from {_file}')
        else:
            self.master.log.insert_log(f'Error importing char config from {_file}')

    def _export_char_config(self):
        _file = self._select_save_file()
        print('exporting char config to %s', _file)
        self.master._functions_frame.save_config().save_file(_file)
        self.master.log.insert_log(f'Exporting char config to {_file}')

    def _select_open_file(self):
        data_path = os.environ.get('HOME', os.environ.get('LOCALAPPDATA'))
        return filedialog.askopenfilenames(
            parent=self.master,
            initialdir=os.path.join(data_path, 'GhostBot'),
            initialfile='tmp',
            filetypes=[
                ("Yaml", "*.yml"),
                ("All files", "*")
            ]
        )

    def _select_save_file(self):
        data_path = os.environ.get('HOME', os.environ.get('LOCALAPPDATA'))
        return filedialog.asksaveasfilename(
            parent=self.master,
            defaultextension=".yml",
            initialdir=os.path.join(data_path, 'GhostBot'),
            initialfile='char_config.yml',
            filetypes=[
                ("Yaml", "*.yml"),
                ("All files", "*")
            ]
        )

def main():
    import logging

    if os.environ.get('PYCHARM_HOSTED'):
        logger.setLevel(logging.DEBUG)

    ghost_bot = GhostBot()

    def _on_char_change():
        if _selected := ghost_bot.selected_char():
            ghost_bot.client.char_info(_selected)
            time.sleep(0.1)
            ghost_bot.client.get_config(_selected)

    def _refresh_char_info():
        while True:
            time.sleep(1)
            if _selected := ghost_bot.selected_char():
                ghost_bot.client.char_info(_selected)

    ghost_bot.list_box.on_list_select(lambda _: _on_char_change())
    threading.Thread(target=_refresh_char_info, daemon=True).start()

    ghost_bot.mainloop()

if __name__ == '__main__':
    main()