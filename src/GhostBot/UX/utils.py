from pathlib import Path
from tkinter import ttk
import tkinter as tk

from GhostBot.UX import theme as T


# bot images root folder (used by icon capture)
_IMAGES_ROOT = Path(__file__).resolve().parent.parent / "Images"


class Tooltip:
    """Simple tooltip that appears when hovering over a widget."""
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _=None):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.tip, text=self.text, bg="#ffffe0", fg="#1A1A1A", relief="solid", borderwidth=1,
            font=("TkDefaultFont", 13), padx=8, pady=5, justify="left",
        ).pack()

    def _hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


def _format_spot(_spot: str | tuple[int, int]):
    if _spot:
        if isinstance(_spot, str):
            return tuple(_spot.split(" "))
        return f"{' '.join(map(str, _spot))}"
    return ''

type VarConfig = tuple[str, type[str | bool]]

def create_entry(
        widget: tk.Misc,
        label: str,
        row: int,
        column: int,
        var_config: VarConfig = None,
        entry_width: int = None,
        hint: str = None,
        bg: str = None,
) -> tk.Variable:

    v_name, v_type = var_config
    if v_type is str:  # Entry
        var = tk.StringVar(master=widget, name=v_name, value="")
        if bg:
            _label_widget = tk.Label(master=widget, text=label, anchor="w", bg=bg)
        else:
            _label_widget = ttk.Label(master=widget, text=label, anchor="w")
        _label_widget.grid(row=row, column=column, padx=4, pady=2, sticky="w")
        entry_kwargs = {"master": widget, "textvariable": var, "takefocus": False, "justify": "center"}
        if entry_width is not None:
            entry_kwargs["width"] = entry_width
        else:
            entry_kwargs["width"] = 10
        if bg:
            entry_kwargs["bg"] = bg
        _entry = tk.Entry(**entry_kwargs)
        _entry.grid(row=row, column=column + 1, padx=2, pady=2, sticky="w")
        if hint:
            Tooltip(_label_widget, hint)
            Tooltip(_entry, hint)

    elif v_type is bool:  # Checkbutton
        var = tk.BooleanVar(master=widget, name=v_name, value=False)
        # width follows the label (min 13) -- otherwise long labels were TRUNCATED (e.g. "Tamer's Pet (")
        _cb = ttk.Checkbutton(master=widget, text=label, variable=var, width=max(len(str(label)) + 2, 13))
        _cb.grid(row=row, column=column, padx=4, pady=2, sticky="w")
        if hint:
            Tooltip(_cb, hint)

    else:
        raise TypeError(f"v_type must be str or bool, not {type(v_type)}")

    return var


def create_int_slider(
        widget: tk.Misc,
        label: str,
        row: int,
        column: int,
        var_name: str,
        default: int = 30,
        min_val: int = 0,
        max_val: int = 100,
        suffix: str = "%",
        hint: str = None,
        bg: str = None,
) -> tk.Variable:
    """Min-max slider + editable Entry synced together. Var stores string for compatibility with extract_config."""
    var = tk.StringVar(master=widget, name=var_name, value=str(default))

    if bg:
        _label_widget = tk.Label(master=widget, text=label, anchor="w", bg=bg)
    else:
        _label_widget = ttk.Label(master=widget, text=label, anchor="w")
    _label_widget.grid(row=row, column=column, padx=4, pady=2, sticky="w")

    scale = ttk.Scale(
        master=widget,
        from_=min_val,
        to=max_val,
        orient="horizontal",
        length=210,
    )

    max_digits = len(str(max_val))

    def _validate(value):
        if value == "":
            return True
        if not value.isdigit() or len(value) > max_digits:
            return False
        return int(value) <= max_val

    vcmd = (widget.register(_validate), "%P")
    pct_entry_kwargs = dict(
        master=widget, textvariable=var, width=5, justify="center",
        validate="key", validatecommand=vcmd,
    )
    if bg:
        pct_entry_kwargs["bg"] = bg
    pct_entry = tk.Entry(**pct_entry_kwargs)
    # click = select all (type over without needing to delete)
    pct_entry.bind("<FocusIn>", lambda _e: pct_entry.after(1, lambda: pct_entry.select_range(0, "end")))
    if bg:
        pct_suffix = tk.Label(master=widget, text=suffix, anchor="w", bg=bg)
    else:
        pct_suffix = ttk.Label(master=widget, text=suffix, anchor="w")

    _updating = {"flag": False}

    def _on_scale(value):
        if _updating["flag"]:
            return
        try:
            v = int(float(value))
        except ValueError:
            v = default
        _updating["flag"] = True
        try:
            var.set(str(v))
        finally:
            _updating["flag"] = False

    def _on_var_change(*_):
        if _updating["flag"]:
            return
        raw = var.get()
        if raw == "":
            return  # user clearing to type new value -- don't touch the slider
        try:
            v = int(float(raw))
        except ValueError:
            return
        v = max(min_val, min(max_val, v))
        _updating["flag"] = True
        try:
            scale.set(v)
            # normalize stored value to int (e.g. "30.0" from config float -> "30")
            if str(v) != raw:
                var.set(str(v))
        finally:
            _updating["flag"] = False

    def _on_focus_out(_=None):
        # on focus loss, ensure var has a valid value between min-max
        raw = var.get()
        if raw == "":
            var.set(str(default))
            return
        try:
            v = max(min_val, min(max_val, int(float(raw))))
            if str(v) != raw:
                var.set(str(v))
        except ValueError:
            var.set(str(default))

    scale.config(command=_on_scale)
    var.trace_add("write", _on_var_change)
    pct_entry.bind("<FocusOut>", _on_focus_out)
    pct_entry.bind("<Return>", _on_focus_out)
    scale.set(default)

    scale.grid(row=row, column=column + 1, padx=2, pady=2, sticky="w")
    pct_entry.grid(row=row, column=column + 2, padx=(2, 0), pady=2, sticky="w")
    pct_suffix.grid(row=row, column=column + 3, padx=(0, 2), pady=2, sticky="w")

    if hint:
        # Tooltip on hover over slider or label, instead of occupying fixed space
        Tooltip(scale, hint)
        Tooltip(_label_widget, hint)
        Tooltip(pct_entry, hint)

    return var


def create_percent_slider(widget, label, row, column, var_name, default=30):
    """Wrapper of create_int_slider for 0-100% (compatibility)."""
    return create_int_slider(widget, label, row, column, var_name, default, min_val=0, max_val=100, suffix="%")


def setup_drag_from_listbox(listbox: tk.Listbox, on_drop):
    """Allows dragging an item from the listbox to another widget. Shows a blue 'ghost' following the cursor.
    on_drop(item_text, target_widget_under_cursor, source_index) is called on release."""
    state = {"item": None, "ghost": None, "idx": None}

    def _start(event):
        idx = listbox.nearest(event.y)
        if idx >= 0:
            try:
                state["item"] = listbox.get(idx)
                state["idx"] = idx
            except tk.TclError:
                state["item"] = None

    def _motion(event):
        if not state["item"]:
            return
        if state["ghost"] is None:
            g = tk.Toplevel(listbox)
            g.wm_overrideredirect(True)
            g.attributes("-alpha", 0.85)
            tk.Label(g, text=state["item"], bg=T.GREEN, fg="white",
                     padx=8, pady=4, font=("TkDefaultFont", 11, "bold")).pack()
            state["ghost"] = g
        state["ghost"].geometry(f"+{event.x_root + 12}+{event.y_root + 12}")

    def _end(event):
        if state["ghost"]:
            state["ghost"].destroy()
            state["ghost"] = None
        if state["item"] is not None:
            target = listbox.winfo_containing(event.x_root, event.y_root)
            on_drop(state["item"], target, state["idx"])
            state["item"] = None
            state["idx"] = None

    listbox.bind("<Button-1>", _start)
    listbox.bind("<B1-Motion>", _motion)
    listbox.bind("<ButtonRelease-1>", _end)


def widget_in_container(widget, container) -> bool:
    """True if widget is a descendant of container (or is the container itself)."""
    while widget is not None:
        if widget == container:
            return True
        widget = widget.master
    return False


class ScrollableFrame(tk.Frame):
    """Container with VERTICAL scroll for the entire tab. Put content inside `.inner`.
    Content takes full width (no horizontal scroll) and scrolls vertically when needed."""

    def __init__(self, parent, bg: str = None, **kwargs):
        bg = bg or T.BG_MAIN
        super().__init__(parent, bg=bg, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vbar.set)
        self.vbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        # scrollregion follows content; inner follows canvas width (no horizontal scroll)
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        # mouse wheel scrolls, but only when cursor is over this tab
        self.canvas.bind("<Enter>", lambda _e: self.canvas.bind_all("<MouseWheel>", self._on_wheel))
        self.canvas.bind("<Leave>", lambda _e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_wheel(self, event):
        # only scroll if content is LARGER than the visible area (otherwise "scroll up" pushed
        # content to the middle leaving empty space at top). If everything fits, lock at top.
        try:
            bbox = self.canvas.bbox("all")
            if not bbox:
                return
            content_h = bbox[3] - bbox[1]
            if content_h <= self.canvas.winfo_height():
                self.canvas.yview_moveto(0)
                return
            self.canvas.yview_scroll(int(-event.delta / 120), "units")
        except tk.TclError:
            pass


def capture_icon_dialog(parent, folder: Path, on_saved=None):
    """
    Popup to capture TO item icon via Win+Shift+S.

    `folder`: folder inside Images/ where the BMP will be saved (e.g. SELL, ALERTS/RARE).
    `on_saved(item_name)`: optional callback called after the BMP is saved.
    """
    folder.mkdir(parents=True, exist_ok=True)

    # Lazy import of PIL to avoid circular import or issues if PIL isn't installed yet
    try:
        from PIL import ImageGrab, ImageTk
    except ImportError:
        tk.messagebox.showerror("Pillow missing", "Install Pillow: pip install pillow")
        return

    win = tk.Toplevel(parent)
    win.title(f"Capture icon -> {folder.name}")
    win.geometry("420x340")
    win.transient(parent)
    win.grab_set()
    win.configure(bg=T.BG_PANEL)

    state = {"img": None, "preview_label": None}

    tk.Label(win, text=f"Saving to: Images/{folder.relative_to(_IMAGES_ROOT)}",
             bg=T.BG_PANEL, fg=T.FG_MUTED, font=("TkDefaultFont", 11)).pack(pady=(8, 4))

    tk.Label(win, text="Item name (no spaces, no .bmp):",
             bg=T.BG_PANEL, font=("TkDefaultFont", 12)).pack(pady=(8, 2))
    name_entry = tk.Entry(win, width=30, justify="center")
    name_entry.pack(pady=2)
    name_entry.focus_set()

    instr = tk.Label(
        win,
        text="1. Go to the game\n2. Win+Shift+S, crop ONLY the icon\n3. Come back here and click 'Read clipboard'",
        bg=T.BG_PANEL, fg=T.FG_MUTED, justify="left", font=("TkDefaultFont", 11),
    )
    instr.pack(pady=(8, 4))

    preview_holder = tk.Frame(win, bg=T.BG_INPUT, bd=1, relief="solid", width=120, height=90)
    preview_holder.pack(pady=4)
    preview_holder.pack_propagate(False)
    state["preview_label"] = tk.Label(preview_holder, text="(preview)", bg=T.BG_INPUT, fg=T.FG_MUTED)
    state["preview_label"].pack(expand=True)

    status = tk.Label(win, text="", bg=T.BG_PANEL, fg=T.GREEN_HI, font=("TkDefaultFont", 11))
    status.pack(pady=(2, 4))

    def _read_clipboard():
        img = ImageGrab.grabclipboard()
        if img is None or isinstance(img, list):
            status.config(text="Clipboard has no image. Use Win+Shift+S first.", fg="#c62828")
            return
        state["img"] = img.convert("RGB")
        # scaled preview to fit in the 120x90 box
        ph_w, ph_h = 116, 86
        ratio = min(ph_w / img.width, ph_h / img.height, 3)
        new_size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
        preview = state["img"].resize(new_size)
        photo = ImageTk.PhotoImage(preview)
        state["preview_label"].configure(image=photo, text="")
        state["preview_label"].image = photo  # keep ref
        status.config(text=f"Captured: {img.width}x{img.height} -- now click Save",
                      fg=T.GREEN_HI)

    def _save():
        if state["img"] is None:
            status.config(text="Crop and click 'Read clipboard' before saving.", fg="#c62828")
            return
        name = name_entry.get().strip()
        if not name or "/" in name or "\\" in name or name.startswith("."):
            status.config(text="Invalid name (no spaces, no slashes, no leading dot).", fg="#c62828")
            return
        bmp_path = folder / f"{name}.bmp"
        if bmp_path.exists():
            from tkinter import messagebox
            if not messagebox.askyesno("Overwrite?", f"{name}.bmp already exists. Overwrite?",
                                       parent=win):
                return
        state["img"].save(bmp_path, format="BMP")
        if on_saved is not None:
            try:
                on_saved(name)
            except Exception:
                pass
        win.destroy()

    btn_bar = tk.Frame(win, bg=T.BG_PANEL)
    btn_bar.pack(pady=8)
    ttk.Button(btn_bar, text="Read clipboard", command=_read_clipboard).pack(side="left", padx=4)
    ttk.Button(btn_bar, text="Save", command=_save, style="Accent.TButton").pack(side="left", padx=4)
    ttk.Button(btn_bar, text="Cancel", command=win.destroy).pack(side="left", padx=4)


class NamedListWidget:
    """Simple listbox with input + add/remove buttons. Used for name lists (items, etc.).

    If `capture_folder` is passed, shows a '+ Capture icon' button that opens a dialog to
    save a BMP of the item icon in that folder.
    """

    def __init__(self, parent, title: str, grid_row: int, grid_column: int,
                 width: int = 22, height: int = 7, title_color: str = T.FG_MAIN,
                 hint: str = None, capture_folder: Path | None = None):
        self.container = tk.Frame(parent, bd=1, relief="solid", bg=T.BG_PANEL)
        self.container.grid(row=grid_row, column=grid_column, padx=4, pady=4, sticky="nw")
        self._capture_folder = capture_folder

        _title_lbl = tk.Label(self.container, text=title, bg=T.BG_PANEL, fg=title_color,
                              font=("TkDefaultFont", 10, "bold"))
        _title_lbl.pack(side="top", anchor="w", padx=6, pady=(4, 2))
        if hint:
            Tooltip(_title_lbl, hint)

        self.listbox = tk.Listbox(self.container, width=width, height=height,
                                  bg=T.BG_INPUT, borderwidth=0, highlightthickness=0,
                                  selectbackground=T.GREEN, selectforeground=T.BG_PANEL)
        self.listbox.pack(side="top", padx=4, pady=2)

        entry_frame = tk.Frame(self.container, bg=T.BG_PANEL)
        entry_frame.pack(side="top", fill="x", padx=4, pady=(2, 4))

        self._entry = tk.Entry(entry_frame, width=width - 6)
        self._entry.pack(side="left", padx=(0, 2))
        self._entry.bind("<Return>", lambda _e: self.add_from_entry())

        ttk.Button(entry_frame, text="+", width=2, command=self.add_from_entry).pack(side="left", padx=1)
        ttk.Button(entry_frame, text="×", width=2, command=self.remove_selected).pack(side="left", padx=1)

        if capture_folder is not None:
            cap_btn = ttk.Button(self.container, text="📷 Capture icon", command=self._open_capture)
            cap_btn.pack(side="top", padx=4, pady=(0, 6), fill="x")
            Tooltip(cap_btn, f"Capture a BMP of a game item (Win+Shift+S) and save to Images/{capture_folder.name}/")

    def _open_capture(self):
        capture_icon_dialog(self.container, self._capture_folder, on_saved=self.add_item)

    def add_from_entry(self):
        value = self._entry.get().strip()
        if value:
            self.listbox.insert("end", value)
            self._entry.delete(0, "end")

    def remove_selected(self):
        for i in reversed(self.listbox.curselection()):
            self.listbox.delete(i)

    def get_items(self) -> list[str]:
        return list(self.listbox.get(0, "end"))

    def set_items(self, items: list[str]):
        self.listbox.delete(0, "end")
        for it in (items or []):
            self.listbox.insert("end", it)

    def add_item(self, value: str):
        if value and value not in self.get_items():
            self.listbox.insert("end", value)


class ComboWidget:
    """Dynamic combo widget: user adds/removes rows of (key, interval ms).
    Container with fixed height (~5 visible lines) + vertical scroll when exceeded."""

    VISIBLE_HEIGHT_PX = 180  # ~6 visible lines

    def __init__(self, parent, label_text: str, grid_row: int, grid_column: int, hint: str = None, show_tab_button: bool = True):
        self.parent = parent
        self.hint = hint
        self.rows = []
        self._show_tab_button = show_tab_button

        _label = ttk.Label(parent, text=label_text, anchor="w")
        _label.grid(row=grid_row, column=grid_column, sticky="nw", padx=4, pady=4)
        if hint:
            Tooltip(_label, hint)

        self.container = ttk.Frame(parent)
        self.container.grid(row=grid_row, column=grid_column + 1, columnspan=8, sticky="nw", padx=4, pady=2)

        # Rows stack directly here (no own scroll) -- the ENTIRE TAB scrolls now.
        self._inner = ttk.Frame(self.container)
        self._inner.pack(side="top", fill="x", anchor="w")

        # Buttons at the base of the container
        self._btn_bar = ttk.Frame(self.container)
        self._btn_bar.pack(side="top", anchor="w", pady=(4, 2))

        self._add_btn = ttk.Button(self._btn_bar, text="+ Add key", command=self.add_row)
        self._add_btn.pack(side="left", padx=(0, 4))

        if self._show_tab_button:
            self._tab_btn = ttk.Button(self._btn_bar, text="+ TAB (switch target)",
                                       command=lambda: self.add_row("tab", "500"))
            self._tab_btn.pack(side="left")
            Tooltip(self._tab_btn, "Adds a row with the TAB key to switch targets. Useful for kiting multiple mobs before AOE.")

    def add_row(self, key: str = "", interval: str = ""):
        row_frame = ttk.Frame(self._inner)
        row_frame.pack(side="top", fill="x", pady=1, anchor="w")

        num_label = ttk.Label(row_frame, text="?", width=3, anchor="e")
        num_label.grid(row=0, column=0, padx=(0, 4))

        ttk.Label(row_frame, text="Key").grid(row=0, column=1)
        key_var = tk.StringVar(value=key)
        key_entry = tk.Entry(row_frame, textvariable=key_var, width=5, justify="center")
        key_entry.grid(row=0, column=2, padx=2)

        ttk.Label(row_frame, text="Interval").grid(row=0, column=3, padx=(8, 2))
        int_var = tk.StringVar(value=interval)
        int_entry = tk.Entry(row_frame, textvariable=int_var, width=6, justify="center")
        int_entry.grid(row=0, column=4, padx=2)
        ttk.Label(row_frame, text="ms").grid(row=0, column=5)

        rm_btn = ttk.Button(row_frame, text="×", width=3, command=lambda: self._remove(row_frame))
        rm_btn.grid(row=0, column=6, padx=(8, 0))

        if self.hint:
            Tooltip(key_entry, self.hint)
            Tooltip(int_entry, self.hint)

        self.rows.append({'frame': row_frame, 'key_var': key_var, 'int_var': int_var, 'num_label': num_label})
        self._renumber()

    def _remove(self, row_frame):
        for i, r in enumerate(self.rows):
            if r['frame'] == row_frame:
                row_frame.destroy()
                self.rows.pop(i)
                break
        self._renumber()

    def _renumber(self):
        for i, r in enumerate(self.rows):
            r['num_label'].config(text=f"{i + 1}°")

    def get_attacks(self) -> list:
        attacks = []
        for r in self.rows:
            k = r['key_var'].get().strip()
            interval = r['int_var'].get().strip()
            if k and interval:
                try:
                    attacks.append([k, int(interval)])
                except ValueError:
                    pass
        return attacks

    def set_attacks(self, attacks: list):
        for r in self.rows:
            r['frame'].destroy()
        self.rows = []
        for entry in (attacks or []):
            try:
                k, interval = entry
                self.add_row(str(k) if k is not None else "", str(interval) if interval is not None else "")
            except (TypeError, ValueError):
                pass
        if not self.rows:
            self.add_row()


def create_combo_slots(
        parent,
        label_text: str,
        start_row: int,
        column: int,
        name_prefix: str,
        num_slots: int = 5,
        hint: str = None,
) -> list:
    """N rows of (Key, Interval ms). Returns list of (key_var, interval_var)."""
    _header = ttk.Label(master=parent, text=label_text, anchor="ne")
    _header.grid(row=start_row, column=column, padx=4, pady=2, sticky="ne", rowspan=num_slots)
    if hint:
        Tooltip(_header, hint)

    vars_list = []
    for i in range(num_slots):
        row = start_row + i
        key_var = tk.StringVar(master=parent, name=f"{name_prefix}.{i}.key", value="")
        int_var = tk.StringVar(master=parent, name=f"{name_prefix}.{i}.interval", value="")

        # "N°"
        ttk.Label(master=parent, text=f"{i+1}°", anchor="e", width=3).grid(row=row, column=column+1, padx=2)

        # Key [_]
        ttk.Label(master=parent, text="Key", anchor="e").grid(row=row, column=column+2)
        _key_entry = tk.Entry(master=parent, textvariable=key_var, width=3, justify="center")
        _key_entry.grid(row=row, column=column+3, padx=2)

        # Interval [____] ms
        ttk.Label(master=parent, text="Interval").grid(row=row, column=column+4)
        _int_entry = tk.Entry(master=parent, textvariable=int_var, width=6, justify="center")
        _int_entry.grid(row=row, column=column+5, padx=2)
        ttk.Label(master=parent, text="ms").grid(row=row, column=column+6)

        if hint:
            Tooltip(_key_entry, hint)
            Tooltip(_int_entry, hint)

        vars_list.append((key_var, int_var))

    return vars_list
