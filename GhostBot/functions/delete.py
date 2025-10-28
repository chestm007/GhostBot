from __future__ import annotations

import time

from typing import TYPE_CHECKING

from GhostBot.functions import Runner
from GhostBot.image_finder import ImageFinder
from GhostBot.lib.math import seconds

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient


class Delete(Runner):
    def __init__(self, client: ExtendedClient):
        super().__init__(client)
        self._image_finder = ImageFinder(client)
        self._interval = self._client.config.delete.interval or 10
        self._delete_trash = self._client.config.delete.delete_trash or False
        #self._last_time_ran = time.time()
        self._last_time_ran = 0

    def _run(self):
        if not self._should_delete():
            return
        self._log_info("running delete function")
        self._last_time_ran = time.time()

        if self._delete_trash:
            self._log_info("Deleting trash")
            self._run_delete_trash()

    def _run_delete_trash(self):
        self._client.open_inventory()
        time.sleep(1)
        for item_pos in self._image_finder.find_items_in_window(self._image_finder.items):
            self._client.left_click(item_pos)
            self._client.left_click(self._image_finder.destroy_item_location)
            time.sleep(0.3)
            ok_pos = self._image_finder._get_dialog_ok_location(self._client)
            if ok_pos:
                self._client.left_click(ok_pos)
        self._client.close_inventory()

    def _should_delete(self):
        return time.time() - self._last_time_ran > seconds(minutes=self._interval)
