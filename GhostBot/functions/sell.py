from __future__ import annotations
import time
from _operator import sub
from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.config import SellConfig
from GhostBot.functions import Locational
from GhostBot.lib.math import seconds, item_coordinates_from_pos, linear_distance
from GhostBot.lib.talisman_ui_locations import UI_locations

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


class Sell(Locational):
    def __init__(self, client: ExtendedClient):
        super().__init__(client)
        self._client = client
        self.config: SellConfig = client.config.sell

        if (_return_spot := self.config.return_spot) is None:
            _return_spot = self.determine_start_location()
        self._return_spot = _return_spot

        self._last_time_sold = time.time()
        #self._last_time_sold = 0

    def _run(self):
        if not self._should_sell():
            return
        self._last_time_sold = time.time()

        if not self._go_to_npc():
            return False

        time.sleep(2)
        self._sell_items()

        time.sleep(2)
        self._path_to_attack_spot()
        return True

    def _go_to_npc(self):
        self._path_to_npc_search_spot()
        self._client.search_surroundings(self.config.sell_npc_name)
        first_result = self._client.pointers.get_sur_info()
        logger.info(first_result)
        if self.config.sell_npc_name in first_result.get('name'):
            npc_location = tuple(map(int, first_result.get('coords').split(',')))
            self._client.goto_first_surrounding_result()
            while (dist := linear_distance(self._client.location, npc_location)) > 2 and self._client.running:
                time.sleep(0.5)
            return True
        return False

    def _sell_items(self):
        self._client.reset_camera()
        time.sleep(2)
        self._client.click_npc()
        time.sleep(1)
        self._client.left_click(UI_locations.sell_item_button)
        time.sleep(1)
        for i in range(24):
            self._client.left_click(
                item_coordinates_from_pos(
                    int(self.config.sell_item_pos),
                    UI_locations.sell_item_slot_1
                )
            )
            time.sleep(0.25)
        self._client.left_click(UI_locations.confirm_sell_button)

    def _path_to_npc_search_spot(self):
        if self.config.npc_search_spot is not None:
            self._map_toggle()
            logger.info(f'pathing to npc search spot: {self.config.npc_search_spot}')
            self._client.right_click(tuple(map(sub, self.config.npc_search_spot, (50, 50))))
            self._client.right_click(self.config.npc_search_spot)
            time.sleep(0.5)
            self._map_toggle()
            while self._client.running and linear_distance(self._client.location, self.config.npc_search_spot) > 20:
                _location = self._client.location
                time.sleep(3)
                if linear_distance(self._client.location, _location) < 1:
                    break

    def _path_to_attack_spot(self):
        if self.config.return_spot is not None:
            self._map_toggle()
            logger.info(f'returning to {self._return_spot}')
            self._client.right_click(tuple(map(sub, self.config.return_spot, (50, 50))))
            self._client.right_click(self.config.return_spot)
            time.sleep(0.5)
            self._map_toggle()
            while self._client.running and linear_distance(self._client.location, self.start_location) > 40:
                time.sleep(1)

    def _should_sell(self) -> bool:
        return time.time() - self._last_time_sold > seconds(minutes=self.config.sell_interval_mins)

    def _map_toggle(self):
        self._client.press_key('m')
        time.sleep(0.5)

#if __name__ == "__main__":
#    proc = pymem.Pymem(5732)
#    client = ExtendedClient(proc)
#
#    config = Config(sell=SellConfig(
#        sell_npc_name="Blacksmith",
#        sell_item_pos=1,
#        sell_npc_pos=(0, 0)
#
#    ))
#
#    client.config= config
#
#    client.running = True
#    sell = Sell(client)
#    sell._run()