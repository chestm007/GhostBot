from __future__ import annotations

import contextlib
import json
import threading
import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk

from GhostBot.UX.pyuiWidgets.listBox import ScrollableListbox
from GhostBot.IPC.message import Message
from GhostBot.IPC.message import Command
from GhostBot.UX.utils import create_entry
from GhostBot.config import LoginDetailsConfigLoader
from GhostBot.lib.var_or_none import var_or_none
from GhostBot.server import GhostbotIPCClient



char_info_refresh_lock = threading.RLock()

class GhostBotAutoLogin(tk.Toplevel):
    def __init__(self, *args, client, **kwargs):
        super().__init__(*args, **kwargs)
        self.client: GhostbotIPCClient = client
        self.geometry("600x400")
        self.title("Auto Login")

        self._char_list = tk.Variable(master=self)

        self.client.add_callback(Command.INFO_AUTOLOGIN, self.set_char_list)

        self.list_box = ScrollableListbox(parent=self, scrollx=False, scrolly=True, listvariable=self._char_list)
        self.list_box.config(bg="#646464", fg="#eaeaea", width=20, height=24)
        self.display_frame = tk.Frame(master=self)
        self.display_frame.config()
        self._vars = dict(
            char_name=create_entry(self.display_frame, "Char Name:", 0, 0, ("autologin.char_name", str)),
            username=create_entry(self.display_frame, "Username: ", 1, 0, ("autologin.username", str)),
            password=create_entry(self.display_frame, "Password:", 2, 0, ("autologin.password", str)),
            server=create_entry(self.display_frame, "Server:", 3, 0, ("autologin.server", str)),
            enabled=tk.BooleanVar(master=self, name="autologin.enabled", value=False),
        )
        ttk.Checkbutton(master=self.display_frame, text="Enable autologin", style="TCheckbutton", variable=self._vars['enabled']).grid(row=4, column=0, columnspan=2)

        def save_config():
            _config = LoginDetailsConfigLoader.CharDetails(
                char_name=var_or_none(self.getvar('autologin.char_name'), str),
                username=var_or_none(self.getvar('autologin.username'), str),
                password=var_or_none(self.getvar('autologin.password'), str),
                server=var_or_none(self.getvar('autologin.server'), str),
                enabled=var_or_none(self.getvar('autologin.enabled'), bool),
            )
            self.client.set_config_autologin(_config)
        ttk.Button(master=self, text="Save", width=10, command=save_config).place(x=500, y=350)

        def _new_func():
            self._char_list.set(
                list(self._char_list.get())
                + [tk.simpledialog.askstring('New char name', 'Enter Name: ')]
            )
        ttk.Button(master=self, text="New", width=10, command=_new_func).place(x=420, y=350)

        def _delete_func():
            if _selected := self.selected_char():
                self.client.delete_config_autologin(_selected)
        ttk.Button(master=self, text="Delete", width=10, command=_delete_func).place(x=340, y=350)

        def _close_func():
            if _selected := self.selected_char():
                self.client.close_client(_selected)
        ttk.Button(master=self, text="Close", width=10, command=_close_func).place(x=220, y=350)

        def _open_func():
            if _selected := self.selected_char():
                self.client.open_client(_selected)
        ttk.Button(master=self, text="Login", width=10, command=_open_func).place(x=140, y=350)

        self.list_box.grid(row=0, column=0)
        self.list_box.on_list_select(self._on_char_change)
        self.display_frame.grid(row=0, column=1)

        print(self.client.list_chars_autologin())
        self.client.add_callback(Command.CONFIG_AUTOLOGIN_GET, self.update_login_config_display)
        self.client.add_callback(Command.CONFIG_AUTOLOGIN_DELETE, self._delete_from_char_list)

    def update_login_config_display(self, message: Message):
        response = json.loads(message.target)
        if not response:
            self.setvar('autologin.enabled', False)
            self.setvar('autologin.char_name', '')
            self.setvar('autologin.username', '')
            self.setvar('autologin.password', '')
            self.setvar('autologin.server', '')
            print('fukt')
            return
        with contextlib.suppress(RuntimeError):
            char_info_refresh_lock.release()
        if self.selected_char() == response['char_name']:
            self.setvar('autologin.char_name', response.get('char_name', 'loading.'))
            self.setvar('autologin.username', response.get('username', 'loading.'))
            self.setvar('autologin.password', response.get('password', 'loading.'))
            self.setvar('autologin.server', response.get('server', 'loading.'))
            self.setvar('autologin.enabled', bool(response.get('enabled', False)))

    def selected_char(self):
        with contextlib.suppress(tk.TclError):
            if _selection_list := self.list_box.curselection():
                return self.list_box.get(_selection_list[0])

    def _on_char_change(self, _):
        if _selected := self.selected_char():
            char_info_refresh_lock.acquire()
            self.client.get_config_autologin(_selected)

    def set_char_list(self, message: Message):
        self._char_list.set(message.target.split(' '))

    def _delete_from_char_list(self, message: Message):
        _chars = list(self._char_list.get())
        print(_chars)
        _chars.remove(message.target['char'])
        print(_chars)
        self._char_list.set(_chars)

    def destroy(self):
        self.client.del_callback(Command.INFO_AUTOLOGIN, self.set_char_list)
        self.client.del_callback(Command.CONFIG_AUTOLOGIN_GET, self.update_login_config_display)
        self.client.add_callback(Command.CONFIG_AUTOLOGIN_DELETE, self._delete_from_char_list)
        super().destroy()
