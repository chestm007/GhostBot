__all__ = ['AbstractClientWindow']

import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Self

from GhostBot import logger as _logger
from GhostBot.image_finder import ImageFinder
from GhostBot.lib.types import Location
from GhostBot.lib.talisman_ui_locations import UI_locations


class AbstractClientWindow(ABC):
    """
    Abstract Class containing all methods expected to interact with the Talisman Online client window.
    """
    def __init__(self):
        self.logger = _logger.getChild(self.__class__.__name__)
        self._image_finder = ImageFinder(self)

    @property
    @abstractmethod
    def identifier(self) -> str: ...

    @property
    @abstractmethod
    def window_handle(self) -> int: ...

    @abstractmethod
    def set_window_name(self) -> Self: ...

    @property
    def has_alive_target(self):
        try:
            if self.target_hp < 0:
                return False
        except TypeError:
            return False
        if self.target_name == self.name:
            return False
        return True

    def new_target(self, _key='tab') -> Self:
        self.press_key(_key)
        return self

    def target_self(self, _key='F1') -> Self:
        self.press_key(_key)
        return self

    def sit(self, _key='x') -> Self:
        self.press_key(_key)
        return self

    @property
    @abstractmethod
    def disconnected(self) -> bool: ...

    @abstractmethod
    def on_mount(self) -> bool: ...

    @contextmanager
    def mounted(self, _key=None):
        if _key is None:
            yield
            return

        self.mount(_key)
        yield
        self.dismount(_key)

    def mount(self, _key=None):
        if _key is None:
            return

        attempts = 0
        while not self.on_mount and attempts < 3:
            attempts += 1
            self.press_key(_key)
            time.sleep(4)
        if attempts == 3:
            self.logger.error("Failed to mount up")

    def dismount(self, _key=None):
        if _key is None:
            return

        attempts = 0
        while self.on_mount and attempts < 3:
            attempts += 1
            self.press_key(_key)
            time.sleep(4)
        if attempts == 3:
            self.logger.error("Failed to dismount")

    @abstractmethod
    def capture_window(self, color: bool = False): ...

    @abstractmethod
    def press_key(self, key: int | str, char_only: bool = False) -> None: ...

    def type_keys(self, keys: str, char_only: bool = False) -> None:
        for key in keys.swapcase():
            self.press_key(key, char_only=char_only)

    @abstractmethod
    def left_click(self, pos: tuple[float, float]) -> None: ...

    @abstractmethod
    def right_click(self, pos: tuple[float, float]) -> None: ...

    @staticmethod
    @abstractmethod
    def get_mouse_window_pos(window_pos: tuple[int, int]) -> Location | None: ...

    @abstractmethod
    def get_window_size_pos(self) -> tuple[Location, Location] | None: ...

    def get_window_pos(self) -> Location:
        return self.get_window_size_pos()[0]

    def get_window_size(self) -> Location:
        return self.get_window_size_pos()[1]

    def _resolve_button_pos(self, bmp_name: str, fallback: tuple[int, int],
                            threshold: float = 0.75) -> tuple[int, int]:
        """
        Tenta achar um botao na janela via template matching de Images/misc/<bmp_name>.
        Se nao achar (BMP ausente ou match abaixo do threshold), retorna a coord `fallback`
        hardcoded (de UI_locations) -- assim o bot continua funcionando ate o usuario
        capturar o BMP.
        """
        pos = self._image_finder.find_button_center(bmp_name, threshold=threshold)
        if pos is None:
            self.logger.info("%s nao achado por template, usando coord fallback %s", bmp_name, fallback)
            return fallback
        self.logger.info("%s achado por template em %s", bmp_name, pos)
        return pos

    # ============================================================
    # POSICOES DA UI (descobertas via find_anchor.py / where_is_cursor.py)
    # ============================================================
    #
    # A HUD do TO esta "anchored to corners" -- ela nao escala com tamanho de
    # janela, fica colada no canto. Pra cada elemento da UI a gente sabe:
    #   - qual canto da janela ele ancora
    #   - offset (x, y) fixo em pixels a partir desse canto
    #
    # Pra ADICIONAR um botao novo: rode tools/find_anchor.py, posicione mouse
    # no botao, ele te diz qual canto e qual offset.
    #
    # CONVENCAO de coordenadas: CLIENT coord (sem barra de titulo, sem borda).
    # ============================================================

    # Botao do olho no minimapa (top-right anchor)
    _MINIMAP_SURROUNDINGS_OFFSET_RIGHT = 49
    _MINIMAP_SURROUNDINGS_OFFSET_TOP = 60

    # Botao de reset de camera/view (top-right anchor)
    _VIEW_RESET_OFFSET_RIGHT = 157
    _VIEW_RESET_OFFSET_TOP = 55

    # NPC / char position (CENTER anchor -- char fica sempre centralizado na tela).
    # Apos reset_camera + NPC selecionado via surroundings, o NPC fica em cima
    # do char (mesmo lugar). Offset eh do centro da janela.
    _NPC_LOCATION_OFFSET_X = -19
    _NPC_LOCATION_OFFSET_Y = +21

    # ------------------------------------------------------------
    # Offsets ANCORADOS EM TEMPLATE (calibrados via cursor 2026-05-24).
    # A gente acha um elemento fixo (titulo do painel) via matchTemplate e
    # calcula o resto por offset. Funciona em qualquer posicao/tamanho de janela.
    # O Δ da barra de titulo (captura=window coords, clique=client coords) se
    # CANCELA porque o offset foi medido como (cursor_client - centro_template).
    # ------------------------------------------------------------
    _ANCHOR_THRESHOLD = 0.70

    # Painel Surroundings (ancora: Images/misc/surroundings_title.bmp)
    _SURR_TO_SEARCH = (140, 347)        # titulo -> campo de busca dourado
    _SURR_TO_RESULT = (-106, 70)        # titulo -> 1o resultado da lista

    # Janela "Dialogue" do NPC (ancora: npc_dialogue_title.bmp)
    _DIALOGUE_TO_SELL_ITEM = (-114, 181)  # titulo "Dialogue" -> botao "Sell Item"

    # Dialog de venda (ancora: npc_sell_dialog_header.bmp). Grid 6 col x 4 linhas = 24 slots.
    _SELL_TO_SLOT1 = (-97, 43)          # header -> slot 1 (top-left do grid)
    _SELL_COL_SPACING = 34.4
    _SELL_ROW_SPACING = 35.333
    _SELL_TO_CONFIRM = (-76, 461)       # header -> botao confirmar venda

    # Mapa (ancora: map_title.bmp). Bug do jogo: 2 cliques no mesmo destino nao andam,
    # entao da um clique-isca numa regiao diferente antes do spot real.
    _MAP_DUMMY_OFFSET = (60, 0)

    def open_surroundings_ui(self):
        ww, _ = self.get_window_size()
        pos = (ww - self._MINIMAP_SURROUNDINGS_OFFSET_RIGHT,
               self._MINIMAP_SURROUNDINGS_OFFSET_TOP)
        self.logger.info("open_surroundings_ui: window_width=%d, pos calculada=%s", ww, pos)
        self.left_click(pos)
        time.sleep(1.5)

    def map_open(self) -> bool:
        return self._image_finder.is_map_open()

    @contextmanager
    def map(self):
        self.open_map()
        yield
        self.close_map()

    def open_map(self):
        while not self.map_open():
            self.press_key('m')

    def close_map(self):
        while self.map_open():
            self.press_key('m')

    @property
    @abstractmethod
    def inventory_open(self) -> bool: ...

    @contextmanager
    def inventory(self):
        self.open_inventory()
        yield
        self.close_inventory()

    def open_inventory(self):
        while not self.inventory_open:
            self.press_key('i')
            time.sleep(1)

    def close_inventory(self):
        while self.inventory_open:
            self.press_key('i')
            time.sleep(1)

    def _find_anchor(self, bmp_name: str) -> tuple[int, int] | None:
        """Centro de um template (titulo de painel) na janela; None se nao achar."""
        return self._image_finder.find_button_center(bmp_name, threshold=self._ANCHOR_THRESHOLD)

    def search_surroundings(self, val):
        # acha o titulo "Surroundings"; se nao achar, painel fechado -> abre e tenta de novo
        title = self._find_anchor('surroundings_title.bmp')
        if title is None:
            self.open_surroundings_ui()
            title = self._find_anchor('surroundings_title.bmp')
        if title is None:
            self.logger.error("search_surroundings: titulo 'Surroundings' nao achado (painel visivel?)")
            return
        search = (title[0] + self._SURR_TO_SEARCH[0], title[1] + self._SURR_TO_SEARCH[1])
        self.logger.info("search_surroundings: titulo %s -> campo de busca %s, digitando '%s'", title, search, val)
        self.left_click(search)
        time.sleep(0.5)
        for _ in range(15):            # limpa texto anterior (senao acumula 'XX' nas reexecucoes)
            self.press_key('backspace')
        time.sleep(0.3)
        self.type_keys(val)
        time.sleep(1.0)

    def goto_first_surrounding_result(self):
        title = self._find_anchor('surroundings_title.bmp')
        if title is None:
            self.logger.error("goto_first_surrounding_result: titulo 'Surroundings' nao achado")
            return
        result = (title[0] + self._SURR_TO_RESULT[0], title[1] + self._SURR_TO_RESULT[1])
        self.logger.info("goto_first_surrounding_result: titulo %s -> resultado %s", title, result)
        self.left_click(result)

    def close_surroundings_ui(self):
        # fecha o painel SO se ainda estiver aberto (clicar no resultado pode te-lo fechado)
        if self._find_anchor('surroundings_title.bmp') is not None:
            self.open_surroundings_ui()  # toggle do olho do minimapa

    def click_npc(self):
        # NPC fica em cima do char, que esta sempre no centro da tela.
        ww, wh = self.get_window_size()
        pos = (ww // 2 + self._NPC_LOCATION_OFFSET_X,
               wh // 2 + self._NPC_LOCATION_OFFSET_Y)
        self.logger.info("click_npc: window=%dx%d, pos calculada=%s", ww, wh, pos)
        self.right_click(pos)

    def click_npc_sell_button(self):
        # acha o titulo "Dialogue" da janela do NPC e clica em "Sell Item" por offset
        dlg = self._find_anchor('npc_dialogue_title.bmp')
        if dlg is None:
            self.logger.error("click_npc_sell_button: 'Dialogue' nao achado (janela do NPC visivel?)")
            return False
        sell_item = (dlg[0] + self._DIALOGUE_TO_SELL_ITEM[0], dlg[1] + self._DIALOGUE_TO_SELL_ITEM[1])
        self.logger.info("click_npc_sell_button: 'Dialogue' %s -> Sell Item %s", dlg, sell_item)
        self.left_click(sell_item)
        return True

    def reset_camera(self):
        ww, _ = self.get_window_size()
        pos = (ww - self._VIEW_RESET_OFFSET_RIGHT, self._VIEW_RESET_OFFSET_TOP)
        self.logger.info("reset_camera: window_width=%d, pos calculada=%s", ww, pos)
        self.left_click(pos)

    # ------------------------------------------------------------
    # Dialog de venda (ancora: header "Sell") + grid de 24 slots (6 col x 4 linhas)
    # ------------------------------------------------------------
    def sell_dialog_header(self) -> tuple[int, int] | None:
        """Centro do titulo 'Sell' do dialog de venda. None se nao aberto/visivel."""
        return self._find_anchor('npc_sell_dialog_header.bmp')

    def sell_slot_pos(self, header: tuple[int, int], n: int) -> tuple[int, int]:
        """Posicao do slot n (1-24) do grid de venda, ancorada no header."""
        idx = n - 1
        row, col = idx // 6, idx % 6
        return (int(header[0] + self._SELL_TO_SLOT1[0] + col * self._SELL_COL_SPACING),
                int(header[1] + self._SELL_TO_SLOT1[1] + row * self._SELL_ROW_SPACING))

    def sell_confirm_pos(self, header: tuple[int, int]) -> tuple[int, int]:
        return (header[0] + self._SELL_TO_CONFIRM[0], header[1] + self._SELL_TO_CONFIRM[1])

    def goto_spot_via_map(self, spot_map_offset: tuple[int, int]) -> bool:
        """
        Abre o mapa (M), clica no spot de farm (clique-isca numa regiao diferente +
        o spot real, pra furar o bug do jogo de clique repetido no mesmo destino) e
        fecha o mapa. A espera de chegada fica no chamador (sell.py).
        `spot_map_offset` = offset a partir do titulo 'Map' (escolhido pelo usuario na UI).
        """
        self.press_key('m')
        time.sleep(2.0)
        title = self._find_anchor('map_title.bmp')
        if title is None:
            self.press_key('m')   # tenta abrir de novo
            time.sleep(2.0)
            title = self._find_anchor('map_title.bmp')
        if title is None:
            self.logger.error("goto_spot_via_map: 'Map' nao achado (mapa abriu?)")
            return False
        spot = (title[0] + spot_map_offset[0], title[1] + spot_map_offset[1])
        dummy = (spot[0] + self._MAP_DUMMY_OFFSET[0], spot[1] + self._MAP_DUMMY_OFFSET[1])
        self.logger.info("goto_spot_via_map: 'Map' %s -> isca %s -> spot %s", title, dummy, spot)
        self.right_click(dummy)
        time.sleep(0.5)
        self.right_click(spot)
        time.sleep(0.5)
        self.press_key('m')   # fecha o mapa pra liberar o movimento
        return True

    @abstractmethod
    def team_size(self) -> int: ...

    @property
    @abstractmethod
    def team_members(self) -> list[str]: ...

    @property
    @abstractmethod
    def pet_active(self) -> bool: ...

    @property
    @abstractmethod
    def hp(self) -> int: ...

    @property
    @abstractmethod
    def max_hp(self) -> int: ...

    @property
    @abstractmethod
    def mana(self) -> int: ...

    @property
    @abstractmethod
    def max_mana(self) -> int: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def level(self) -> int: ...

    @property
    @abstractmethod
    def sitting(self) -> bool: ...

    @property
    @abstractmethod
    def in_battle(self) -> str: ...

    @property
    @abstractmethod
    def location(self) -> Location: ...

    @property
    def location_x(self) -> int:
        """
        character location * 20, usually also off by .5
        :returns character location as it appears in game
        """
        return self.location.x

    @property
    def location_y(self) -> int:
        """
        character location * 20, usually also off by .5
        :returns character location as it appears in game
        """
        return self.location.y

    @property
    @abstractmethod
    def location_name(self) -> str | None: ...

    @property
    @abstractmethod
    def target_location(self) -> Location | None: ...

    @property
    @abstractmethod
    def target_id(self) -> str: ...

    @property
    @abstractmethod
    def notification(self) -> bool: ...

    @property
    @abstractmethod
    def has_target(self) -> bool: ...

    @property
    @abstractmethod
    def target_hp(self) -> int | None: ...

    @property
    @abstractmethod
    def target_name(self) -> str | None: ...
