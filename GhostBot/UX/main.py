import os
import tkinter as tk
from tkinter import ttk

from GhostBot.UX.tabbed_widget.delete_frame import DeleteFrame
from GhostBot.UX.tabbed_widget.sell_frame import SellFrame
from GhostBot.server import IPCClient

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
        self.client = IPCClient()
        self.title("GhostBot")
        self.config(bg="#545454")
        self.geometry("700x490")

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure("attack.TCheckbutton", background="#E4E2E2", foreground="#000")
        self.style.map("attack.TCheckbutton", background=[("active", "#E4E2E2")], foreground=[("active", "#000")])

        self.menu = GhostBotMenu(self)
        self.config(menu=self.menu)

class GhostBotMenu (tk.Menu):
    def __init__(self, master):
        super().__init__(master)

        menu_0 = tk.Menu(self, tearoff=0)
        menu_0.add_command(label="New", command=lambda: print("New clicked"))
        menu_0.add_command(label="Open", command=lambda: print("Open clicked"))
        menu_0.add_command(label="Shutdown Server", command=self.master.client.shutdown_server)
        menu_0.add_command(label="Exit", command=self.master.destroy)
        self.add_cascade(label="File", menu=menu_0)

        menu_1 = tk.Menu(self, tearoff=0)
        menu_1.add_command(label="About")
        self.add_cascade(label="Help", menu=menu_1)

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    ghost_bot = GhostBot()




    _char_list = tk.StringVar(master=ghost_bot)
    _char_list.set(ghost_bot.client.list_chars())
    list_box = ScrollableListbox(parent=ghost_bot, scrollx=False, scrolly=True, listvariable=_char_list)

    list_box.config(bg="#646464", fg="#eaeaea")
    list_box.place(x=7, y=9, width=163, height=439)

    def selected_char():
        try:
            return list_box.get(list_box.curselection())
        except tk.TclError:
            return None

    tabbed_widget = TabbedWidget(ghost_bot, enable_reorder=False)
    tabbed_widget.config()
    tabbed_widget.place(x=177, y=9, width=508, height=230)

    _functions_frame = FunctionsFrame(master=tabbed_widget)
    _attack_frame = AttackFrame(master=tabbed_widget)
    _buff_frame = BuffFrame(master=tabbed_widget)
    _fairy_frame = FairyFrame(master=tabbed_widget)
    _pet_frame = PetFrame(master=tabbed_widget)
    _regen_frame = RegenFrame(master=tabbed_widget, client=ghost_bot.client)
    _sell_frame = SellFrame(master=tabbed_widget)
    _delete_frame = DeleteFrame(master=tabbed_widget)

    tabbed_widget.add(_functions_frame, text="Functions")
    tabbed_widget.add(_attack_frame, text="Attack")
    tabbed_widget.add(_fairy_frame, text="Fairy")
    tabbed_widget.add(_buff_frame, text="Buff")
    tabbed_widget.add(_regen_frame, text="Regen")
    tabbed_widget.add(_pet_frame, text="Pet")
    tabbed_widget.add(_sell_frame, text="Sell")
    tabbed_widget.add(_delete_frame, text="Delete")

    log = LogWindow(master=ghost_bot)
    log.config(bg="#fff", fg="#000")
    log.place(x=177, y=248, width=508, height=200)
    #tabbed_widget.setvar("char_info.name", "Ch35TY")

    ttk.Button(
        master=ghost_bot, text="Start", command=lambda: ghost_bot.client.start_bot(selected_char())
    ).place(x=410, y=450)
    ttk.Button(
        master=ghost_bot, text="Stop", command=lambda: ghost_bot.client.stop_bot(selected_char())
    ).place(x=500, y=450)

    def save_config():
        ghost_bot.client.set_config(
            target=_functions_frame.getvar('char_info.name'),
            config=_functions_frame.save_config()
        )

    ttk.Button(master=ghost_bot, text="Save", width=10, command=save_config).place(x=590, y=450)

    def update_char_info_display(trigger=False):
        if trigger:
            list_box.after(1000, update_char_info_display, True)
        try:
            if selected_char():
                response = ghost_bot.client.char_info(selected_char()).target
            else:
                response = {}
        except tk.TclError:
            return

        tabbed_widget.setvar("char_info.name", response.get("name", 'loading.'))
        tabbed_widget.setvar("char_info.level", response.get("level", 'loading.'))
        tabbed_widget.setvar("char_info.location_name", response.get("location_name", 'loading.'))
        tabbed_widget.setvar("char_info.hp", f"{response.get("hp")}/{response.get("max_hp")}")
        tabbed_widget.setvar("char_info.mana", f"{response.get("mana")}/{response.get("max_mana")}")
        tabbed_widget.setvar("char_info.target_name", response.get("target_name", 'loading.'))
        tabbed_widget.setvar("char_info.target_hp", response.get("target_hp", 'loading.'))
        tabbed_widget.setvar("char_info.position", f"({response.get("location_x")}, {response.get("location_y")})")
        tabbed_widget.setvar("char_info.status", response.get("status", 'loading.'))
        tabbed_widget.setvar("window_info.pos", response.get("window_pos", ''))
        tabbed_widget.setvar("window_info.size", response.get("window_size", ''))


    def on_char_change():
        update_char_info_display()
        if selected_char():
            bot_config = ghost_bot.client.get_config(selected_char())
            print(bot_config)

            tabbed_widget.setvar("bot_config.attack.enabled", bool(bot_config.attack))
            tabbed_widget.setvar("bot_config.pet.enabled", bool(bot_config.pet))
            tabbed_widget.setvar("bot_config.buff.enabled", bool(bot_config.buff))
            tabbed_widget.setvar("bot_config.regen.enabled", bool(bot_config.regen))
            tabbed_widget.setvar("bot_config.fairy.enabled", bool(bot_config.fairy))
            tabbed_widget.setvar('bot_config.sell.enabled', bool(bot_config.sell))

            _attack_frame.display_config(bot_config)
            _buff_frame.display_config(bot_config)
            _fairy_frame.display_config(bot_config)
            _pet_frame.display_config(bot_config)
            _regen_frame.display_config(bot_config)
            _sell_frame.display_config(bot_config)
            _delete_frame.display_config(bot_config)


    list_box.on_list_select(lambda _: on_char_change())
    update_char_info_display(trigger=True)


    ghost_bot.mainloop()

if __name__ == '__main__':
    main()