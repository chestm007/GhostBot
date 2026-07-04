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
    NUM_SELL_BAGS = 3   # 24-item bags -> reopen dialog each round

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
            self._log_err('return_spot_map_offset not set -- cannot return to spot')

        #self._last_time_sold = time.time()
        self._last_time_sold = 0

    def _force_run(self) -> bool:
        """Sell request OUTSIDE the interval (e.g. inventory full detected by
        monitor). Consumes the flag -> Sell runs on the next main loop turn,
        sequential with Attack (no fighting over the char). Normal timer still applies."""
        if getattr(self._client, 'sell_requested', False):
            self._client.sell_requested = False
            self._log_info("sell requested (inventory full) -- selling now")
            return True
        return False

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
        self._client.set_action("🏃 Going to sell (NPC)")
        # STARTS in Surroundings (DO NOT use the old move_to_pos/map here -- it would open
        # the map and click random coords at the start).
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
        self._client.close_surroundings_ui()   # close panel on arrival
        time.sleep(2)                            # let char settle
        return True

    def _sell_items(self):
        self._client.set_action("💰 Selling at NPC")
        self._log_info('Selling...')
        start_slot = int(self.config.sell_item_pos or 1)
        self._client.reset_camera()
        time.sleep(2)
        for bag in range(self.NUM_SELL_BAGS):
            if not self._client.running:
                return
            self._client.click_npc()              # open NPC Dialogue window
            time.sleep(2)
            if not self._client.click_npc_sell_button():   # find "Dialogue" -> click "Sell Item"
                self._log_err('NPC window / Sell Item not found (visible/on left?)')
                return
            time.sleep(2)
            header = self._client.sell_dialog_header()     # find "Sell" title
            if header is None:
                self._log_err('Sell dialog did not open ("Sell" header not found)')
                return
            slot = self._client.sell_slot_pos(header, start_slot)
            self._log_info('Bag %d/%d: clicking slot %d at %s (30x)',
                           bag + 1, self.NUM_SELL_BAGS, start_slot, str(slot))
            for _ in range(30):                    # reflow: sell from initial slot onward
                if not self._client.running:       # Stop = emergency: abort immediately
                    self._log_info('Stop pressed during selling -- aborting')
                    return
                self._client.left_click(slot)
                time.sleep(0.2)
            if not self._client.running:           # do not confirm partial sell after Stop
                return
            self._client.left_click(self._client.sell_confirm_pos(header))   # CONFIRM the sell
            time.sleep(2)                          # confirm -> dialog closes

    def _path_to_attack_spot(self):
        if not self._client.running:   # Stop pressed -> do not even try to return to spot
            return
        self._client.set_action("🏃 Returning to spot (post-sell)")
        # spot offset on map: priority to ATTACK config (where it is now),
        # falls back to sell for compatibility with old configs.
        _atk = self._client.config.attack
        offset = (getattr(_atk, 'return_spot_map_offset', None) if _atk else None) or self.config.return_spot_map_offset
        if offset is None:
            self._log_err('return_spot_map_offset not set (neither Attack nor Sell) -- skipping return to spot')
            return
        self._log_info('Returning to farm spot %s', str(self._return_spot))
        self._client.goto_spot_via_map(tuple(offset))   # open map -> bait + spot -> close map
        time.sleep(2)   # give char time to START walking before checking movement
        # ARRIVED = stopped walking (or already close). The old '> 3' was too tight:
        # map click stops 5-15 short of the point, never hit <=3, and char stayed 60s
        # idle at spot without resuming attack. block_while_moving unblocks on stop/arrival.
        self._client.block_while_moving(self._return_spot)
