from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING

from GhostBot.functions import Runner
from GhostBot.functions.runner import run_at_interval
from GhostBot.image_finder import ImageFinder
from GhostBot.lib.math import seconds

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow


@run_at_interval(run_on_start=True)
class Delete(Runner):
    def __init__(self, client: BotClientWindow):
        super().__init__(client)
        self._image_finder = ImageFinder(client)
        self._interval = seconds(minutes=self._client.config.delete.interval or 10)
        self._delete_trash = self._client.config.delete.delete_trash or False

    async def _run(self):
        self._log_info("running delete function")

        if self._delete_trash:
            self._log_info("Deleting trash")
            await self._run_delete_trash()

    async def _run_delete_trash(self):
        async with self._client.inventory():
            for item_pos in self._image_finder.find_items_in_window(self._image_finder.items):
                await self._client.left_click(item_pos)
                await self._client.left_click(self._image_finder.destroy_item_location)
                await asyncio.sleep(0.3)
                ok_pos = self._image_finder.dialog_ok_location
                if ok_pos:
                    await self._client.left_click(ok_pos)

if __name__ == "__main__":
    import os
    for k, v in os.environ.items():
        print(k, v)
