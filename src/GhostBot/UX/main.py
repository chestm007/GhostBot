import contextlib
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import font as tkfont

from GhostBot import logger
from GhostBot.UX import theme as T
from GhostBot.UX.utils import ScrollableFrame
from GhostBot.UX.autologin.main import GhostBotAutoLogin
from GhostBot.UX.tabbed_widget.sell_frame import SellFrame
from GhostBot.config import Config
from GhostBot.IPC.message import Command
from GhostBot.server import GhostbotIPCClient

from GhostBot.UX.pyuiWidgets.logWindow import LogWindow
from GhostBot.UX.pyuiWidgets.listBox import ScrollableListbox
from GhostBot.UX.pyuiWidgets.tabbedWidget import TabbedWidget

from GhostBot.UX.tabbed_widget.attack_frame import AttackFrame
from GhostBot.UX.tabbed_widget.boss_frame import BossFrame
from GhostBot.UX.tabbed_widget.fairy_frame import FairyFrame
from GhostBot.UX.tabbed_widget.functions import FunctionsFrame
from GhostBot.UX.tabbed_widget.pet_frame import PetFrame


class GhostBot(tk.Tk):
    def __init__(self):
        # AppUserModelID: makes Windows use the app icon (not Python's) in the taskbar
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("TalismanBot.GhostBot")
        except Exception:
            pass
        super().__init__()
        self.client = GhostbotIPCClient()
        self.title("Talisman Bot")
        # window icon (logo). In the .exe the icon comes from nuitka; here it's for when running via python.
        try:
            _ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Images", "logo.ico")
            if os.path.exists(_ico):
                self.iconbitmap(_ico)
        except Exception:
            pass

        # Fonts +2 app-wide: increases default named fonts (affects widgets that don't
        # set an explicit font -- tabs, buttons, labels, entries, lists, menus).
        for _fname in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            try:
                tkfont.nametofont(_fname).configure(size=12)
            except tk.TclError:
                pass

        # Dark palette (Talisman Bot theme) -- colors centralized in UX/theme.py
        BG_MAIN = T.BG_MAIN
        BG_PANEL = T.BG_PANEL
        BG_LIST = T.BG_LIST
        FG_LIST = T.FG_MAIN
        ACCENT = T.GREEN

        self.config(bg=BG_MAIN)
        self.geometry("1040x720")
        self.minsize(820, 560)

        # Defaults for classic tk widgets (Entry/Listbox/Label/Frame/Toplevel/Scrollbar)
        # to stay dark automatically, without needing to set color on each one.
        self.option_add("*Font", "TkDefaultFont 12")
        self.option_add("*background", BG_MAIN)
        self.option_add("*foreground", T.FG_MAIN)
        self.option_add("*Entry.background", T.BG_INPUT)
        self.option_add("*Entry.foreground", T.FG_MAIN)
        self.option_add("*Entry.insertBackground", T.FG_MAIN)
        self.option_add("*Listbox.background", T.BG_INPUT)
        self.option_add("*Listbox.foreground", T.FG_MAIN)
        self.option_add("*Listbox.selectBackground", T.GREEN)
        self.option_add("*Listbox.selectForeground", "#0E1714")
        self.option_add("*Text.background", T.BG_INPUT)
        self.option_add("*Text.foreground", T.FG_MAIN)
        self.option_add("*Toplevel.background", BG_MAIN)
        self.option_add("*Scrollbar.background", BG_PANEL)
        self.option_add("*Scrollbar.troughColor", T.BG_INPUT)
        self.option_add("*Scrollbar.activeBackground", T.GREEN)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Global larger font + dark base
        _default_font = ("TkDefaultFont", 12)
        self.style.configure(".", font=_default_font, background=BG_MAIN, foreground=T.FG_MAIN,
                             fieldbackground=T.BG_INPUT, bordercolor=T.BORDER,
                             lightcolor=BG_PANEL, darkcolor=BG_PANEL)

        # Button/label styles
        self.style.configure("TButton", padding=6, relief="solid", borderwidth=1,
                             bordercolor=T.GREEN, background=BG_PANEL, foreground=T.FG_MAIN)
        self.style.map("TButton", background=[("active", "#26392F")],
                       bordercolor=[("active", T.GREEN_HI)])
        # Start = green with dark text
        self.style.configure("Accent.TButton", background=T.GREEN, foreground="#0E1714")
        self.style.map("Accent.TButton", background=[("active", T.GREEN_HI)])
        # Stop = red (emergency button)
        self.style.configure("Stop.TButton", background=T.RED, foreground="#ffffff")
        self.style.map("Stop.TButton", background=[("active", "#B83232")])
        self.style.configure("TLabel", background=BG_MAIN, foreground=T.FG_MAIN)
        self.style.configure("TFrame", background=BG_MAIN)
        self.style.configure("TCheckbutton", background=BG_MAIN, foreground=T.FG_MAIN)
        self.style.map("TCheckbutton", background=[("active", BG_MAIN)], foreground=[("active", T.GREEN_HI)])
        self.style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=(12, 6), background=BG_PANEL, foreground=T.FG_MUTED)
        self.style.map("TNotebook.Tab", background=[("selected", T.GREEN)], foreground=[("selected", "#0E1714")])
        # Sliders / combos / scrollbars ttk
        self.style.configure("Horizontal.TScale", background=BG_MAIN, troughcolor=T.BG_INPUT)
        self.style.configure("TCombobox", fieldbackground=T.BG_INPUT, background=BG_PANEL,
                             foreground=T.FG_MAIN, arrowcolor=T.FG_MAIN)
        self.style.configure("TScrollbar", background=BG_PANEL, troughcolor=T.BG_INPUT, arrowcolor=T.FG_MAIN)

        self.style.configure("attack.TCheckbutton", background=BG_MAIN, foreground=T.FG_MAIN)
        self.style.map("attack.TCheckbutton", background=[("active", BG_MAIN)], foreground=[("active", T.GREEN_HI)])

        self.menu = GhostBotMenu(self)
        self.config(menu=self.menu)

        # === RESPONSIVE LAYOUT WITH GRID ===
        # Column 0 (list): fixed width.  Column 1 (tabs/log): expands.
        # Row 0 (tabs+log via PanedWindow): expands.  Row 1 (buttons): fixed height.
        self.grid_columnconfigure(0, weight=0, minsize=180)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self._char_list = tk.Variable(master=self)
        self.client.add_callback(Command.LOG, lambda message: self.log.insert_log(message.target))
        self.client.add_callback(Command.INFO, lambda message: self.set_char_list(message.target.split(' ')))
        self.client.add_callback(Command.INFO_CHAR, lambda message: update_char_info_display(message.target))

        # Left column: logo banner on top + character list below
        left_frame = tk.Frame(self, bg=BG_MAIN)
        left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(6, 3), pady=6)
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        try:
            from PIL import Image, ImageTk
            _logo_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Images", "logo.png")
            _logo_im = Image.open(_logo_png).resize((150, 150), Image.LANCZOS)
            self._logo_img = ImageTk.PhotoImage(_logo_im)
            tk.Label(left_frame, image=self._logo_img, bg=BG_MAIN, borderwidth=0).grid(row=0, column=0, pady=(0, 6))
        except Exception as _e:
            logger.debug("logo banner not loaded: %s", _e)

        self.list_box = ScrollableListbox(parent=left_frame, scrollx=False, scrolly=True, listvariable=self._char_list)
        tk.Frame.configure(self.list_box, bg=BG_MAIN)  # bg of the frame around the list
        self.list_box.config(bg=BG_LIST, fg=FG_LIST, borderwidth=0, highlightthickness=0,
                             selectbackground=ACCENT, selectforeground="#0E1714")
        if hasattr(self.list_box, "v_scroll"):
            self.list_box.v_scroll.configure(bg=BG_PANEL, troughcolor=T.BG_INPUT,
                                             activebackground=T.GREEN, borderwidth=0, highlightthickness=0)
        self.list_box.grid(row=1, column=0, sticky="nsew")

        # Vertical PanedWindow: tabs on top, log below. User drags the divider.
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

        # Each tab goes inside a ScrollableFrame -> the ENTIRE TAB scrolls vertically
        # (not just the combo). Tabs remain accessible via self._*_frame.
        def _make_tab(frame_cls, text, **kw):
            sf = ScrollableFrame(self.tabbed_widget)
            frame = frame_cls(master=sf.inner, **kw)
            frame.pack(fill="both", expand=True)
            self.tabbed_widget.add(sf, text=text)
            return frame

        self._functions_frame = _functions_frame = _make_tab(FunctionsFrame, "Dashboard")
        self._attack_frame = _make_tab(AttackFrame, "Attack")
        self._fairy_frame = _make_tab(FairyFrame, "Fairy")
        self._boss_frame = _make_tab(BossFrame, "Boss")
        self._pet_frame = _make_tab(PetFrame, "Pet")
        self._sell_frame = _make_tab(SellFrame, "Sell", client=self.client)

        self._functions_frame.register_config_frames(
            attack=self._attack_frame,
            fairy=self._fairy_frame,
            boss=self._boss_frame,
            pet=self._pet_frame,
            sell=self._sell_frame,
        )

        def update_char_info_display(response):
            if response.get('name') != self.selected_char():
                return

            self.tabbed_widget.setvar("char_info.name", response.get("name", 'loading.'))
            self.tabbed_widget.setvar("char_info.level", response.get("level", 'loading.'))
            self.tabbed_widget.setvar("char_info.location_name", response.get("location_name", 'loading.'))
            self.tabbed_widget.setvar("char_info.hp", f"{response.get('hp')}/{response.get('max_hp')}")
            self.tabbed_widget.setvar("char_info.mana", f"{response.get('mana')}/{response.get('max_mana')}")
            self.tabbed_widget.setvar("char_info.target_name", response.get("target_name", 'loading.'))
            self.tabbed_widget.setvar("char_info.target_hp", response.get("target_hp", 'loading.'))
            self.tabbed_widget.setvar("char_info.position", f"({response.get('location_x')}, {response.get('location_y')})")
            self.tabbed_widget.setvar("char_info.status", response.get("status", 'loading.'))
            self.tabbed_widget.setvar("window_info.pos", response.get("window_pos", ''))
            self.tabbed_widget.setvar("window_info.size", response.get("window_size", ''))

            # Target HP bar (0-100, -1 = dead/no target)
            t_hp = response.get("target_hp", 0)
            try:
                t_hp_int = int(t_hp) if t_hp is not None else 0
                self._functions_frame.target_hp_bar['value'] = max(0, t_hp_int)
            except (ValueError, TypeError):
                self._functions_frame.target_hp_bar['value'] = 0

            # Battle indicator
            if response.get("in_battle"):
                self._functions_frame.battle_label.config(text="🔴 IN BATTLE", bg="#e04040", fg="white")
            else:
                self._functions_frame.battle_label.config(text="○ Calm", bg=T.BG_PANEL, fg=T.FG_MUTED)

            # Stats (Dashboard)
            self.tabbed_widget.setvar("char_info.kills", str(response.get("kills", 0)))
            self.tabbed_widget.setvar("char_info.farm_time", response.get("farm_time_hms", "00:00:00"))
            _energy = response.get("energy")
            self.tabbed_widget.setvar("char_info.energy", str(_energy) if _energy is not None else "—")
            self.tabbed_widget.setvar("char_info.xp", f"+{response.get('xp_gained', 0)}")
            self.tabbed_widget.setvar("char_info.gold_g", str(response.get("gold_g", 0)))
            self.tabbed_widget.setvar("char_info.gold_s", str(response.get("gold_s", 0)))
            self.tabbed_widget.setvar("char_info.gold_c", str(response.get("gold_c", 0)))

            # Bold bar: bot's current action
            self.tabbed_widget.setvar("char_info.current_action", response.get("current_action", "—"))
            # Session drops panel (list + Want/Don't want buttons)
            self._functions_frame.update_drops(response.get("drops", {}))

        self.client.add_callback(Command.CONFIG, self._update_char_config)

        def save_config():
            self.client.set_config(
                target=_functions_frame.getvar('char_info.name'),
                config=_functions_frame.save_config()
            )

        # Buttons in frame, aligned right
        _btn_frame = ttk.Frame(self)
        _btn_frame.grid(row=1, column=1, sticky="e", padx=(3, 10), pady=(3, 8))
        # Save Status (green = saved / red = failed) -- VISIBLE feedback: before Save
        # failed silently when validation failed on the server.
        self._save_status = tk.Label(_btn_frame, text="", bg=T.BG_MAIN, fg=T.FG_MUTED,
                                     font=("TkDefaultFont", 11), anchor="e", width=22)
        self._save_status.pack(side="left", padx=(0, 8))
        ttk.Button(
            master=_btn_frame, text="Start", style="Accent.TButton",
            command=lambda: self.client.start_bot(self.selected_char())
        ).pack(side="left", padx=2)
        ttk.Button(
            master=_btn_frame, text="Stop", style="Stop.TButton",
            command=lambda: self.client.stop_bot(self.selected_char())
        ).pack(side="left", padx=2)
        ttk.Button(master=_btn_frame, text="Save", width=10, command=save_config).pack(side="left", padx=2)

        self.client.add_callback(Command.CONFIG_GET, lambda message: self._update_char_config(Config.load_yaml(message.target)))

        self.client.add_callback(Command.CONFIG_SET, self._on_config_saved)
        self.client.add_callback(Command.ERROR, self._on_server_error)

        self.client.run()

    def _update_char_config(self, bot_config: Config):

        self.tabbed_widget.setvar("bot_config.attack.enabled", bool(bot_config.attack))
        self.tabbed_widget.setvar("bot_config.pet.enabled", bool(bot_config.pet))
        self.tabbed_widget.setvar("bot_config.fairy.enabled", bool(bot_config.fairy))
        self.tabbed_widget.setvar("bot_config.boss.enabled", bool(bot_config.boss))
        self.tabbed_widget.setvar('bot_config.sell.enabled', bool(bot_config.sell))

        self._attack_frame.display_config(bot_config)
        self._fairy_frame.display_config(bot_config)
        self._boss_frame.display_config(bot_config)
        self._pet_frame.display_config(bot_config)
        self._sell_frame.display_config(bot_config)

    def _set_save_status(self, text: str, color: str):
        try:
            self._save_status.config(text=text, fg=color)
        except tk.TclError:
            pass

    def _on_config_saved(self, message):
        # Server confirmed it saved. Callback runs on IPC thread -> marshals to UI.
        _tgt = message.target if isinstance(message.target, dict) else {}
        _char = _tgt.get("char", "?")
        self.log.insert_log(f'✓ Config saved for {_char}')
        self.after(0, lambda: self._set_save_status(f'✓ Saved {time.strftime("%H:%M:%S")}', T.GREEN_HI))

    def _on_server_error(self, message):
        # Failure from the server (e.g. Save validation). Shows VISIBLE (popup + label).
        _tgt = message.target if isinstance(message.target, dict) else {}
        _char = _tgt.get("char", "?")
        _reason = _tgt.get("reason", "unknown error")
        self.log.insert_log(f'✗ FAILED ({_char}): {_reason}')
        def _show():
            self._set_save_status("✗ Failed — see log", T.RED)
            messagebox.showerror("Save failed",
                                 f"Character: {_char}\n\n{_reason}", parent=self)
        self.after(0, _show)

    def set_char_list(self, _char_list):
        # tk.Variable.get() returns TUPLE for list (or '' if empty); _char_list is LIST.
        # Comparing tuple with list was ALWAYS different -> repopulated listbox every poll
        # -> cleared user selection -> froze the dashboard. Normalize before comparing.
        _cur = self._char_list.get()
        _cur = list(_cur) if isinstance(_cur, (tuple, list)) else []
        _new = list(_char_list)
        if _cur != _new:
            # listvariable's set() REPOPULATES the listbox and CLEARS selection. Preserves the user's
            # selection (by NAME) so we don't deselect/freeze the dashboard when the list
            # changes (e.g. 2nd account logs in, or a char disappears/returns from server scan).
            _selected = self.selected_char()
            self._char_list.set(_char_list)
            if _selected in _new:
                try:
                    _idx = _new.index(_selected)
                    self.list_box.listbox.selection_clear(0, "end")
                    self.list_box.listbox.selection_set(_idx)
                    self.list_box.listbox.activate(_idx)
                except (tk.TclError, ValueError):
                    pass

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
        _tick = 0
        while True:
            time.sleep(1)
            # Request the CHARACTER LIST periodically (~3s) so the interface can
            # AUTO-RECOVER: if it's closed and reopened (or if the char logs in later),
            # the list comes back on its own. Before it only relied on the single "push" the
            # server sends on connection -- if missed, the list stayed empty forever.
            # set_char_list only repopulates if the list changed (no flicker, preserves selection).
            if _tick % 3 == 0:
                ghost_bot.client.list_chars()
            _tick += 1
            if _selected := ghost_bot.selected_char():
                ghost_bot.client.char_info(_selected)

    ghost_bot.list_box.on_list_select(lambda _: _on_char_change())
    threading.Thread(target=_refresh_char_info, daemon=True).start()

    ghost_bot.mainloop()

if __name__ == '__main__':
    main()
