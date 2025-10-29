from __future__ import annotations
import time
from typing import TYPE_CHECKING

from GhostBot.config import SellConfig
from GhostBot.functions import Locational
from GhostBot.functions.runner import run_at_interval
from GhostBot.lib.math import seconds, item_coordinates_from_pos, linear_distance
from GhostBot.lib.talisman_ui_locations import UI_locations

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


@run_at_interval()
class Sell(Locational):
    def __init__(self, client: ExtendedClient):
        super().__init__(client)
        self.config: SellConfig = self._client.config.sell
        self._interval = seconds(minutes=self._client.config.sell.sell_interval_mins)

        if (_return_spot := self.config.return_spot) is None:
            _return_spot = self.determine_start_location()
        self._return_spot = _return_spot

        try:
            self._use_mount = client.config.sell.use_mount
            self._mount_key = client.config.sell.bindings.get('mount')
        except (AttributeError, KeyError):
            self._use_mount = False

        #self._last_time_sold = time.time()
        self._last_time_sold = 0

    def _run(self):
        if self._use_mount:
            self._client.mount(self._mount_key)

        if not self._go_to_npc():
            return False

        time.sleep(2)
        self._sell_items()

        time.sleep(2)
        self._path_to_attack_spot()

        if self._use_mount:
            self._client.dismount(self._mount_key)
        return True

    def _go_to_npc(self):
        self._path_to_npc_search_spot()
        self._client.search_surroundings(self.config.sell_npc_name)
        try:
            first_result = self._client.pointers.get_sur_info()
            if self.config.sell_npc_name in first_result.get('name'):
                npc_location  = tuple(map(float, first_result.get('coords').split(',')))
                self._client.goto_first_surrounding_result()
                while (linear_distance(self._client.location, npc_location)) > 2 and self._client.running:
                    time.sleep(0.5)
        except AttributeError:
            self._log_info("Memory access failed to get npc location, falling back to movement detection :(")
            self._client.goto_first_surrounding_result()
            time.sleep(5)
            self._client.block_while_moving()
        return True

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
        self._client.left_click(UI_locations.confirm_sell_button)

    def _path_to_npc_search_spot(self):
        if self.config.npc_search_spot is not None:
            self._client.move_to_pos(self.config.npc_search_spot)

    def _path_to_attack_spot(self):
        if self.config.return_spot is not None:
            self._log_info(f'returning to {self._return_spot}')
            # TODO: loop trying to move via map until the char moves.
            self._client.move_to_pos(self._return_spot)
            self._goto_start_location()
