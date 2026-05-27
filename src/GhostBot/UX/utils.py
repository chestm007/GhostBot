from pathlib import Path
from tkinter import ttk
import tkinter as tk

from GhostBot.UX import theme as T


# pasta root das imagens do bot (usado pela captura de icones)
_IMAGES_ROOT = Path(__file__).resolve().parent.parent / "Images"


class Tooltip:
    """Tooltip simples que aparece ao passar mouse sobre o widget."""
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
        # largura acompanha o rotulo (min 13) -- senao rotulo longo era CORTADO (ex: "Pet do Tamer (")
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
    """Slider min-max + Entry editavel sincronizada. Var armazena string para compatibilidade com extract_config."""
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
    # clique = seleciona tudo (digita por cima sem precisar apagar)
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
            return  # usuario apagando pra digitar novo valor — nao mexe na barra
        try:
            v = int(float(raw))
        except ValueError:
            return
        v = max(min_val, min(max_val, v))
        _updating["flag"] = True
        try:
            scale.set(v)
            # normaliza valor armazenado pra inteiro (ex: "30.0" do config float -> "30")
            if str(v) != raw:
                var.set(str(v))
        finally:
            _updating["flag"] = False

    def _on_focus_out(_=None):
        # ao perder foco, garante que var tem valor valido entre min-max
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
        # Tooltip ao passar o mouse no slider ou na label, em vez de ocupar espaço fixo
        Tooltip(scale, hint)
        Tooltip(_label_widget, hint)
        Tooltip(pct_entry, hint)

    return var


def create_percent_slider(widget, label, row, column, var_name, default=30):
    """Wrapper de create_int_slider pra 0-100% (compatibilidade)."""
    return create_int_slider(widget, label, row, column, var_name, default, min_val=0, max_val=100, suffix="%")


def setup_drag_from_listbox(listbox: tk.Listbox, on_drop):
    """Permite arrastar item da listbox pra outro widget. Mostra um 'ghost' azul seguindo o cursor.
    on_drop(item_text, target_widget_under_cursor, source_index) é chamado no release."""
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
    """True se widget é descendente de container (ou é o proprio container)."""
    while widget is not None:
        if widget == container:
            return True
        widget = widget.master
    return False


class ScrollableFrame(tk.Frame):
    """Container com scroll VERTICAL pra aba inteira. Coloque o conteudo dentro de `.inner`.
    O conteudo ocupa a largura toda (sem scroll horizontal) e rola na vertical quando precisa."""

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
        # scrollregion acompanha o conteudo; inner acompanha a largura do canvas (sem scroll horizontal)
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        # roda do mouse rola, mas so quando o cursor esta sobre esta aba
        self.canvas.bind("<Enter>", lambda _e: self.canvas.bind_all("<MouseWheel>", self._on_wheel))
        self.canvas.bind("<Leave>", lambda _e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_wheel(self, event):
        # so rola se o conteudo for MAIOR que a area visivel (senao "rolar pra cima" empurrava
        # o conteudo pro meio deixando vazio em cima). Se tudo cabe, trava no topo.
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
    Popup pra capturar icone de item do TO via Win+Shift+S.

    `folder`: pasta dentro de Images/ onde o BMP vai ser salvo (ex: SELL, ALERTS/RARE).
    `on_saved(item_name)`: callback opcional chamado depois que o BMP foi salvo.
    """
    folder.mkdir(parents=True, exist_ok=True)

    # Import lazy do PIL pra nao quebrar import circular ou quem nao tem PIL ainda
    try:
        from PIL import ImageGrab, ImageTk
    except ImportError:
        tk.messagebox.showerror("Pillow ausente", "Instale Pillow: pip install pillow")
        return

    win = tk.Toplevel(parent)
    win.title(f"Capturar icone -> {folder.name}")
    win.geometry("420x340")
    win.transient(parent)
    win.grab_set()
    win.configure(bg=T.BG_PANEL)

    state = {"img": None, "preview_label": None}

    tk.Label(win, text=f"Salvando em: Images/{folder.relative_to(_IMAGES_ROOT)}",
             bg=T.BG_PANEL, fg=T.FG_MUTED, font=("TkDefaultFont", 11)).pack(pady=(8, 4))

    tk.Label(win, text="Nome do item (sem espacos, sem .bmp):",
             bg=T.BG_PANEL, font=("TkDefaultFont", 12)).pack(pady=(8, 2))
    name_entry = tk.Entry(win, width=30, justify="center")
    name_entry.pack(pady=2)
    name_entry.focus_set()

    instr = tk.Label(
        win,
        text="1. Vai pro jogo\n2. Win+Shift+S, recorta SO o icone\n3. Volta aqui e clica 'Ler clipboard'",
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
            status.config(text="Clipboard sem imagem. Use Win+Shift+S primeiro.", fg="#c62828")
            return
        state["img"] = img.convert("RGB")
        # preview escalado pra caber na caixa de 120x90
        ph_w, ph_h = 116, 86
        ratio = min(ph_w / img.width, ph_h / img.height, 3)
        new_size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
        preview = state["img"].resize(new_size)
        photo = ImageTk.PhotoImage(preview)
        state["preview_label"].configure(image=photo, text="")
        state["preview_label"].image = photo  # mantem ref
        status.config(text=f"Capturado: {img.width}x{img.height} -- agora clica Salvar",
                      fg=T.GREEN_HI)

    def _save():
        if state["img"] is None:
            status.config(text="Recorta e clica 'Ler clipboard' antes de salvar.", fg="#c62828")
            return
        name = name_entry.get().strip()
        if not name or "/" in name or "\\" in name or name.startswith("."):
            status.config(text="Nome invalido (sem espacos, sem barras, sem ponto inicial).", fg="#c62828")
            return
        bmp_path = folder / f"{name}.bmp"
        if bmp_path.exists():
            from tkinter import messagebox
            if not messagebox.askyesno("Sobrescrever?", f"{name}.bmp ja existe. Sobrescrever?",
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
    ttk.Button(btn_bar, text="Ler clipboard", command=_read_clipboard).pack(side="left", padx=4)
    ttk.Button(btn_bar, text="Salvar", command=_save, style="Accent.TButton").pack(side="left", padx=4)
    ttk.Button(btn_bar, text="Cancelar", command=win.destroy).pack(side="left", padx=4)


class NamedListWidget:
    """Listbox simples com input + botoes adicionar/remover. Usado pra listas de nomes (itens, etc.).

    Se `capture_folder` for passado, mostra botao '+ Capturar icone' que abre dialog pra
    salvar um BMP do icone do item nessa pasta.
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
            cap_btn = ttk.Button(self.container, text="📷 Capturar icone", command=self._open_capture)
            cap_btn.pack(side="top", padx=4, pady=(0, 6), fill="x")
            Tooltip(cap_btn, f"Capturar BMP de um item do jogo (Win+Shift+S) e salvar em Images/{capture_folder.name}/")

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
    """Widget de combo dinamico: usuario adiciona/remove linhas de (tecla, intervalo ms).
    Container com altura fixa (~5 linhas visiveis) + scroll vertical quando passa disso."""

    VISIBLE_HEIGHT_PX = 180  # ~6 linhas visiveis

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

        # Linhas empilham direto aqui (sem scroll proprio) -- a ABA inteira rola agora.
        self._inner = ttk.Frame(self.container)
        self._inner.pack(side="top", fill="x", anchor="w")

        # Botoes na base do container
        self._btn_bar = ttk.Frame(self.container)
        self._btn_bar.pack(side="top", anchor="w", pady=(4, 2))

        self._add_btn = ttk.Button(self._btn_bar, text="+ Adicionar tecla", command=self.add_row)
        self._add_btn.pack(side="left", padx=(0, 4))

        if self._show_tab_button:
            self._tab_btn = ttk.Button(self._btn_bar, text="+ TAB (trocar alvo)",
                                       command=lambda: self.add_row("tab", "500"))
            self._tab_btn.pack(side="left")
            Tooltip(self._tab_btn, "Adiciona uma linha com a tecla TAB pra trocar de alvo. Útil pra lurar vários mobs antes de AOE.")

    def add_row(self, key: str = "", interval: str = ""):
        row_frame = ttk.Frame(self._inner)
        row_frame.pack(side="top", fill="x", pady=1, anchor="w")

        num_label = ttk.Label(row_frame, text="?", width=3, anchor="e")
        num_label.grid(row=0, column=0, padx=(0, 4))

        ttk.Label(row_frame, text="Tecla").grid(row=0, column=1)
        key_var = tk.StringVar(value=key)
        key_entry = tk.Entry(row_frame, textvariable=key_var, width=5, justify="center")
        key_entry.grid(row=0, column=2, padx=2)

        ttk.Label(row_frame, text="Intervalo").grid(row=0, column=3, padx=(8, 2))
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
            r['num_label'].config(text=f"{i + 1}ª")

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
    """N linhas de (Tecla, Intervalo ms). Retorna lista de (key_var, interval_var)."""
    _header = ttk.Label(master=parent, text=label_text, anchor="ne")
    _header.grid(row=start_row, column=column, padx=4, pady=2, sticky="ne", rowspan=num_slots)
    if hint:
        Tooltip(_header, hint)

    vars_list = []
    for i in range(num_slots):
        row = start_row + i
        key_var = tk.StringVar(master=parent, name=f"{name_prefix}.{i}.key", value="")
        int_var = tk.StringVar(master=parent, name=f"{name_prefix}.{i}.interval", value="")

        # "Nª"
        ttk.Label(master=parent, text=f"{i+1}ª", anchor="e", width=3).grid(row=row, column=column+1, padx=2)

        # Tecla [_]
        ttk.Label(master=parent, text="Tecla", anchor="e").grid(row=row, column=column+2)
        _key_entry = tk.Entry(master=parent, textvariable=key_var, width=3, justify="center")
        _key_entry.grid(row=row, column=column+3, padx=2)

        # Intervalo [____] ms
        ttk.Label(master=parent, text="Intervalo").grid(row=row, column=column+4)
        _int_entry = tk.Entry(master=parent, textvariable=int_var, width=6, justify="center")
        _int_entry.grid(row=row, column=column+5, padx=2)
        ttk.Label(master=parent, text="ms").grid(row=row, column=column+6)

        if hint:
            Tooltip(_key_entry, hint)
            Tooltip(_int_entry, hint)

        vars_list.append((key_var, int_var))

    return vars_list


