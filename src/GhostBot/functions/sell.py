from __future__ import annotations

import time
from typing import TYPE_CHECKING

from GhostBot.functions import Locational
from GhostBot.functions.runner import run_at_interval
from GhostBot.lib.math import seconds, linear_distance

if TYPE_CHECKING:
    from GhostBot.config import SellConfig
    from GhostBot.controller.bot_controller import BotClientWindow


@run_at_interval()
class Sell(Locational):
    NUM_SELL_BAGS = 3   # bags de 24 itens -> reabre o dialog a cada rodada

    def __init__(self, client: BotClientWindow):
        super().__init__(client)
        self.config: SellConfig = self._client.config.sell
        self._interval = seconds(minutes=int(self._client.config.sell.sell_interval_mins))

        self._return_spot = self.determine_start_location()

        try:
            self._use_mount = client.config.sell.use_mount
            self._mount_key = client.config.sell.bindings.get('mount')
        except (AttributeError, KeyError):
            self._log_debug('No mount key set, self._use_mount = False')
            self._use_mount = False

        if self.config.return_spot_map_offset is None:
            self._log_err('return_spot_map_offset nao setado -- nao vai conseguir voltar ao spot')

        #self._last_time_sold = time.time()
        self._last_time_sold = 0

    def _run(self):
        with self._client.mounted(self._mount_key):

            if not self._go_to_npc():
                return False

            time.sleep(2)
            self._sell_items()

            time.sleep(2)
            self._path_to_attack_spot()

            return True

    def _go_to_npc(self):
        self._client.set_action("🏃 Indo vender (NPC)")
        # COMECA no Surroundings (NAO usar o move_to_pos/mapa antigo aqui -- ele abria
        # o mapa e clicava em coord aleatoria no inicio).
        self._client.search_surroundings(self.config.sell_npc_name)
        try:
            first_result = self._client.pointers.get_sur_info()
            if self.config.sell_npc_name in first_result.get('name'):
                coords = first_result.get('coords').split(',')
                npc_location: tuple[int, int] = (int(coords[0]), int(coords[1]))
                self._client.goto_first_surrounding_result()
                self._log_info('Going to npc location %s', str(npc_location))
                while (linear_distance(self._client.location, npc_location)) > 2 and self._client.running:
                    time.sleep(0.5)
            else:
                self._log_info('No npc location found')
        except (AttributeError, TypeError):
            self._log_info("Memory access failed to get npc location, falling back to movement detection :(")
            self._client.goto_first_surrounding_result()
            time.sleep(5)
            self._client.block_while_moving()
        self._client.close_surroundings_ui()   # fecha o painel ao chegar
        time.sleep(2)                            # deixa o char assentar
        return True

    def _sell_items(self):
        self._client.set_action("💰 Vendendo no NPC")
        self._log_info('Vendendo...')
        start_slot = int(self.config.sell_item_pos or 1)
        self._client.reset_camera()
        time.sleep(2)
        for bag in range(self.NUM_SELL_BAGS):
            if not self._client.running:
                return
            self._client.click_npc()              # abre a janela Dialogue do NPC
            time.sleep(2)
            if not self._client.click_npc_sell_button():   # acha "Dialogue" -> clica "Sell Item"
                self._log_err('Janela do NPC / Sell Item nao encontrada (visivel/a esquerda?)')
                return
            time.sleep(2)
            header = self._client.sell_dialog_header()     # acha o titulo "Sell"
            if header is None:
                self._log_err('Dialog de venda nao abriu (header "Sell" nao achado)')
                return
            slot = self._client.sell_slot_pos(header, start_slot)
            self._log_info('Bag %d/%d: clicando slot %d em %s (30x)',
                           bag + 1, self.NUM_SELL_BAGS, start_slot, str(slot))
            for _ in range(30):                    # reflow: vende do slot inicial em diante
                if not self._client.running:       # Stop = emergencia: aborta na hora
                    self._log_info('Stop apertado durante a venda -- abortando')
                    return
                self._client.left_click(slot)
                time.sleep(0.2)
            if not self._client.running:           # nao confirma venda parcial apos Stop
                return
            self._client.left_click(self._client.sell_confirm_pos(header))   # CONFIRMA a venda
            time.sleep(2)                          # confirma -> dialog fecha

    def _path_to_attack_spot(self):
        if not self._client.running:   # Stop apertado -> nem tenta voltar ao spot
            return
        self._client.set_action("🏃 Voltando ao spot (pós-venda)")
        offset = self.config.return_spot_map_offset
        if offset is None:
            self._log_err('return_spot_map_offset nao setado -- pulando retorno ao spot')
            return
        self._log_info('Voltando ao spot de farm %s', str(self._return_spot))
        self._client.goto_spot_via_map(tuple(offset))   # abre mapa -> isca + spot -> fecha mapa
        # espera chegar no spot (coords do mundo = _return_spot, vindo de config.attack.spot)
        t0 = time.time()
        while linear_distance(self._client.location, self._return_spot) > 3 and self._client.running:
            if time.time() - t0 > 60:
                self._log_info('Timeout voltando ao spot')
                break
            time.sleep(1)
