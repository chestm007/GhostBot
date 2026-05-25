import time
from pathlib import Path
from tkinter import ttk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.UX.utils import _format_spot, create_entry, create_int_slider, NamedListWidget, setup_drag_from_listbox, widget_in_container
import tkinter as tk
from GhostBot.client_window import Win32ClientWindow
from GhostBot.config import Config, SellConfig
from GhostBot.lib.var_or_none import var_or_none
from GhostBot.UX import theme as T


_IMAGES_ROOT = Path(__file__).resolve().parent.parent.parent / "Images"


class SellFrame(TabFrame):
    def _init(self, client=None, *args, **kwargs) -> None:
        self._client = client  # IPC client, usado pelo botao 'Vender agora'
        self._vars = dict(
            item_pos=create_entry(
                self, "Slot inicial (1-24):", 0, 0, ("bot_config.sell.item_pos", str), entry_width=8,
                hint="Número do slot por onde começar a vender (1 a 24, da esquerda pra direita, de cima pra baixo). "
                     "Vende desse slot em diante e MANTÉM os anteriores. Ex: pra guardar o slot 1, use 2.",
            ),
            use_mount=create_entry(
                self, "Usar mount:", 0, 2, ("bot_config.sell.use_mount", bool),
                hint="Se marcado, o bot monta a mount pra andar até o NPC mais rápido.",
            ),
            npc_name=create_entry(
                self, "Nome NPC:", 1, 0, ("bot_config.sell.npc_name", str),
                hint="Nome exato do NPC mercador (precisa bater com o que aparece no jogo).",
            ),
            mount_key=create_entry(
                self, "Tecla Mount:", 1, 2, ("bot_config.sell.mount_key", str), entry_width=3,
                hint="Tecla pra montar/desmontar.",
            ),
            npc_search_spot=create_entry(
                self, "Spot busca NPC:", 2, 0, ("bot_config.sell.npc_search_spot", str),
                hint="Coordenadas X,Y de onde o bot começa a procurar o NPC. Use 'Posição atual' pra capturar.",
            ),
            interval_mins=create_int_slider(
                self, "Vender a cada:", 3, 0, "bot_config.sell.interval_mins",
                default=30, min_val=5, max_val=120, suffix="min",
                hint="Frequência da rotina de vender (em minutos). Só roda fora de combate.",
            ),
            return_spot_map_offset=create_entry(
                self, "Spot de farm (mapa):", 4, 0, ("bot_config.sell.return_spot_map_offset", str),
                hint="Pra onde voltar depois de vender. Abra o MAPA (M) no jogo, ponha o mouse no seu spot de farm "
                     "e clique '📍 Capturar spot'. Sem isso o bot não volta pro spot.",
            ),
        )

        ttk.Button(
            master=self, text="Posição atual", command=lambda: self._set_spot_as_current('npc_search_spot')
        ).grid(row=2, column=2, padx=4)

        # Botao "Vender agora" — dispara a rotina de Sell uma vez (bypass intervalo).
        _now_btn = ttk.Button(
            master=self, text="🛒 Vender agora", style="Accent.TButton",
            command=self._on_sell_now,
        )
        _now_btn.grid(row=2, column=3, padx=4, pady=(2, 4), sticky="ew")
        from GhostBot.UX.utils import Tooltip as _Tooltip
        _Tooltip(_now_btn, "Dispara a rotina de Sell imediatamente, sem esperar o intervalo. "
                           "O char precisa estar logado, perto do NPC, fora de combate. "
                           "Recomendado PARAR o bot (botao Stop) antes pra nao dar conflito de cliques.")

        # Botao capturar o spot de farm no MAPA (acha o titulo 'Map' + le o cursor -> offset)
        ttk.Button(
            master=self, text="📍 Capturar spot", command=self._capture_map_spot
        ).grid(row=4, column=2, padx=4)

        # Aviso importante: dialogos do jogo precisam estar visiveis/a esquerda
        _warn = tk.Label(
            self,
            text="⚠️ Deixe os diálogos do jogo (NPC, venda, mapa) à ESQUERDA e VISÍVEIS. "
                 "Se nascerem fora da tela, o bot não os encontra.",
            fg=T.GOLD, bg="#2E2410", wraplength=560, justify="left", anchor="w",
        )
        _warn.grid(row=5, column=0, columnspan=4, padx=4, pady=(6, 4), sticky="ew")

        # Lista de itens da bag (linha 5) — fonte pra drag-and-drop
        self._bag_frame = tk.Frame(self, bd=1, relief="solid", bg=T.BG_PANEL)
        self._bag_frame.grid(row=6, column=0, columnspan=3, padx=4, pady=(10, 2), sticky="ew")

        _bag_title = tk.Label(self._bag_frame, text="📜 Itens na bag — arraste pra categoria abaixo",
                              bg=T.BG_PANEL, fg=T.FG_MAIN, font=("TkDefaultFont", 12, "bold"))
        _bag_title.pack(side="top", anchor="w", padx=8, pady=(6, 2))

        _bag_scroll_frame = tk.Frame(self._bag_frame, bg=T.BG_PANEL)
        _bag_scroll_frame.pack(side="top", fill="x", padx=8, pady=(0, 8))

        self._bag_listbox = tk.Listbox(_bag_scroll_frame, height=5, bg=T.BG_INPUT,
                                       borderwidth=0, highlightthickness=0,
                                       selectbackground=T.GREEN, selectforeground=T.BG_PANEL)
        self._bag_listbox.pack(side="left", fill="x", expand=True)

        _bag_scroll = tk.Scrollbar(_bag_scroll_frame, orient="vertical", command=self._bag_listbox.yview)
        _bag_scroll.pack(side="right", fill="y")
        self._bag_listbox.configure(yscrollcommand=_bag_scroll.set)

        # placeholder enquanto pointer de nomes nao implementado
        self._bag_listbox.insert("end", "(leitura de inventario pendente — task #6)")
        self._bag_listbox.itemconfig(0, fg=T.FG_MUTED)

        # Categorização de itens (linha 6) — destinos do drag-and-drop
        # capture_folder aponta pra pasta onde o BMP do icone vai ser salvo quando
        # o usuario capturar via Win+Shift+S.
        self._items_trash = NamedListWidget(
            self, title="🗑️ Lixo (vender)", grid_row=7, grid_column=0,
            title_color=T.FG_MUTED,
            hint="Itens que o bot vai vender automaticamente quando o inventario estiver cheio.",
            capture_folder=_IMAGES_ROOT / "SELL",
        )
        self._items_keep = NamedListWidget(
            self, title="📦 Bons (manter)", grid_row=7, grid_column=1,
            title_color=T.GREEN_HI,
            hint="Itens valiosos que o bot mantem no inventario sem notificar.",
            capture_folder=_IMAGES_ROOT / "KEEP",
        )
        self._items_rare = NamedListWidget(
            self, title="✨ Super raros (alerta)", grid_row=7, grid_column=2,
            title_color=T.GOLD,
            hint="Itens raros que disparam alerta no Discord quando dropam.",
            capture_folder=_IMAGES_ROOT / "ALERTS" / "RARE",
        )

        # Drag-and-drop: arrastar da bag pra uma das 3 categorias
        setup_drag_from_listbox(self._bag_listbox, self._on_bag_drop)

    def _on_bag_drop(self, item_text, target_widget, source_idx):
        """Chamado quando usuario solta um item arrastado da bag."""
        if item_text.startswith("("):  # placeholder
            return
        for target_list in (self._items_trash, self._items_keep, self._items_rare):
            if widget_in_container(target_widget, target_list.container):
                target_list.add_item(item_text)
                self._bag_listbox.delete(source_idx)
                return

    def update_bag_items(self, items: list[str]):
        """Chamado por main.py quando bot envia INFO_CHAR com lista de itens da bag."""
        self._bag_listbox.delete(0, "end")
        if not items:
            self._bag_listbox.insert("end", "(leitura de inventario pendente — task #6)")
            self._bag_listbox.itemconfig(0, fg=T.FG_MUTED)
            return
        for it in items:
            self._bag_listbox.insert("end", it)

    def _on_sell_now(self) -> None:
        if self._client is None:
            return
        # nome do char vem do dashboard (preenchido quando usuario seleciona na lista)
        char = self.getvar('char_info.name')
        if not char or char == 'loading.':
            return
        self._client.sell_now(char)

    def _set_var_to_mouse_pos(self, field: str) -> None:
        window_pos = self.getvar('window_info.pos')
        self._vars[field].set("Lendo mouse...")
        time.sleep(3)
        mouse_pos = Win32ClientWindow.get_mouse_window_pos(window_pos)
        self._vars[field].set("{} {}".format(*mouse_pos))

    def _set_spot_as_current(self, field: str):
        self._vars[field].set(eval(self.master.getvar('char_info.position')))

    def _capture_map_spot(self):
        """
        Acha o titulo 'Map' na janela do jogo (template) e le o cursor no mesmo
        instante -> salva o OFFSET (cursor_client - titulo). Igual o calibrate.
        Abra o MAPA no jogo e ponha o mouse no spot antes do timer acabar.
        """
        import ctypes
        from ctypes import wintypes
        import win32api
        from GhostBot.lib.win32.process import PymemProcess

        var = self._vars['return_spot_map_offset']
        var.set("Abra o mapa e ponha o mouse no spot...")
        self.update_idletasks()
        time.sleep(4)
        try:
            proc = next(iter(PymemProcess.list_clients()), None)
            if proc is None:
                var.set("(client.exe nao encontrado)")
                return
            client = Win32ClientWindow(proc)
            title = client._image_finder.find_button_center('map_title.bmp', threshold=0.70)
            if title is None:
                var.set("(titulo 'Map' nao achado - mapa aberto/visivel?)")
                return
            sx, sy = win32api.GetCursorPos()
            pt = wintypes.POINT(sx, sy)
            ctypes.windll.user32.ScreenToClient(client.window_handle, ctypes.byref(pt))
            var.set("{} {}".format(pt.x - title[0], pt.y - title[1]))
        except Exception as e:
            var.set(f"(erro: {e})")

    def display_config(self, config: Config):
        if config.sell:
            mount_key = ''
            if config.sell.bindings:
                mount_key = var_or_none(config.sell.bindings.get('mount'))
            self.setvar('bot_config.sell.item_pos', config.sell.sell_item_pos or '')
            self.setvar('bot_config.sell.npc_name', config.sell.sell_npc_name or '')
            self.setvar('bot_config.sell.interval_mins', config.sell.sell_interval_mins or '')
            self.setvar('bot_config.sell.npc_search_spot', _format_spot(config.sell.npc_search_spot))
            self.setvar('bot_config.sell.return_spot_map_offset', _format_spot(config.sell.return_spot_map_offset))
            self.setvar('bot_config.sell.use_mount', bool(config.sell.use_mount))
            self.setvar('bot_config.sell.mount_key', mount_key)
            self._items_trash.set_items(config.sell.items_trash or [])
            self._items_keep.set_items(config.sell.items_keep or [])
            self._items_rare.set_items(config.sell.items_rare or [])
        else:
            self.clear()

    def extract_config(self) -> SellConfig:
        bindings = dict(
            mount=self._nullable_string(self.getvar('bot_config.sell.mount_key')),
        )
        return SellConfig(
            bindings=self._populate_bindings(bindings),
            sell_item_pos=var_or_none(self.getvar('bot_config.sell.item_pos')),
            sell_npc_name=var_or_none(self.getvar('bot_config.sell.npc_name')),
            use_mount=var_or_none(self.getvar('bot_config.sell.use_mount')),
            sell_interval_mins=var_or_none(self.getvar('bot_config.sell.interval_mins')),
            npc_search_spot=var_or_none(self.getvar('bot_config.sell.npc_search_spot')),
            return_spot_map_offset=var_or_none(self.getvar('bot_config.sell.return_spot_map_offset')),
            items_trash=self._items_trash.get_items() or None,
            items_keep=self._items_keep.get_items() or None,
            items_rare=self._items_rare.get_items() or None,
        )
