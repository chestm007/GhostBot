import contextlib
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog

from GhostBot import logger
from GhostBot.UX.autologin.main import GhostBotAutoLogin
from GhostBot.UX.tabbed_widget.delete_frame import DeleteFrame
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


char_info_refresh_lock = threading.RLock()

class GhostBot(tk.Tk):
    def __init__(self):
        super().__init__()
        self.client = GhostbotIPCClient()
        self.title("GhostBot")
        self.config(bg="#545454")
        self.geometry("700x490")

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure("attack.TCheckbutton", background="#E4E2E2", foreground="#000")
        self.style.map("attack.TCheckbutton", background=[("active", "#E4E2E2")], foreground=[("active", "#000")])

        self.menu = GhostBotMenu(self)
        self.config(menu=self.menu)

        self.log = LogWindow(master=self)
        self.log.configure(bg="#fff", fg="#000")
        self.log.place(x=177, y=248, width=508, height=200)

        self.client.add_callback(Command.LOG, lambda message: self.log.insert_log(message.target))

        self._char_list = tk.Variable(master=self)

        self.client.add_callback(Command.INFO, lambda message: self.set_char_list(message.target.split(' ')))
        self.client.add_callback(Command.INFO_CHAR, lambda message: update_char_info_display(message.target))

        # TODO: implement multi select-start
        # list_box = ScrollableListbox(parent=ghost_bot, scrollx=False, scrolly=True, listvariable=_char_list, selectmode=tk.MULTIPLE)
        self.list_box = ScrollableListbox(parent=self, scrollx=False, scrolly=True, listvariable=self._char_list)

        self.list_box.config(bg="#646464", fg="#eaeaea")
        self.list_box.place(x=7, y=9, width=163, height=439)

        self.tabbed_widget = TabbedWidget(self, enable_reorder=False)
        self.tabbed_widget.config()
        self.tabbed_widget.place(x=177, y=9, width=508, height=230)

        _functions_frame = FunctionsFrame(master=self.tabbed_widget)
        self._functions_frame = _functions_frame
        self._attack_frame = AttackFrame(master=self.tabbed_widget)
        self._buff_frame = BuffFrame(master=self.tabbed_widget)
        self._fairy_frame = FairyFrame(master=self.tabbed_widget)
        self._pet_frame = PetFrame(master=self.tabbed_widget)
        self._regen_frame = RegenFrame(master=self.tabbed_widget, client=self.client)
        self._sell_frame = SellFrame(master=self.tabbed_widget)
        self._delete_frame = DeleteFrame(master=self.tabbed_widget)

        self.tabbed_widget.add(_functions_frame, text="Functions")
        self.tabbed_widget.add(self._attack_frame, text="Attack")
        self.tabbed_widget.add(self._fairy_frame, text="Fairy")
        self.tabbed_widget.add(self._buff_frame, text="Buff")
        self.tabbed_widget.add(self._regen_frame, text="Regen")
        self.tabbed_widget.add(self._pet_frame, text="Pet")
        self.tabbed_widget.add(self._sell_frame, text="Sell")
        self.tabbed_widget.add(self._delete_frame, text="Delete")

        def update_char_info_display(response):
            with contextlib.suppress(RuntimeError):
                char_info_refresh_lock.release()
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

        self.client.add_callback(Command.CONFIG, self._update_char_config)

        def save_config():
            self.client.set_config(
                target=_functions_frame.getvar('char_info.name'),
                config=_functions_frame.save_config()
            )

        ttk.Button(
            master=self, text="Start", command=lambda: self.client.start_bot(self.selected_char())
        ).place(x=410, y=450)
        ttk.Button(
            master=self, text="Stop", command=lambda: self.client.stop_bot(self.selected_char())
        ).place(x=500, y=450)

        ttk.Button(master=self, text="Save", width=10, command=save_config).place(x=590, y=450)

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
        self.tabbed_widget.setvar('bot_config.delete.enabled', bool(bot_config.delete))

        self._attack_frame.display_config(bot_config)
        self._buff_frame.display_config(bot_config)
        self._fairy_frame.display_config(bot_config)
        self._pet_frame.display_config(bot_config)
        self._regen_frame.display_config(bot_config)
        self._sell_frame.display_config(bot_config)
        self._delete_frame.display_config(bot_config)

    def set_char_list(self, _char_list):
        if self._char_list.get() != _char_list:
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
    ghost_bot = GhostBot()

    def _on_char_change():
        if _selected := ghost_bot.selected_char():
            char_info_refresh_lock.acquire()
            ghost_bot.client.char_info(_selected)
            time.sleep(0.1)
            ghost_bot.client.get_config(_selected)

    def _refresh_char_info():
        while True:
            time.sleep(1)
            if _selected := ghost_bot.selected_char():
                char_info_refresh_lock.acquire()
                ghost_bot.client.char_info(_selected)

    ghost_bot.list_box.on_list_select(lambda _: _on_char_change())
    threading.Thread(target=_refresh_char_info, daemon=True).start()

    ghost_bot.mainloop()

if __name__ == '__main__':
    import logging

    if os.environ.get('PYCHARM_HOSTED'):
        logger.setLevel(logging.DEBUG)

    main()