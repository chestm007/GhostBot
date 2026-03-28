import asyncio
import time

import pytest

from GhostBot.abstract_client_window import AbstractClientWindow
from GhostBot.controller.async_bot_controller import AsyncBotController

@pytest.skip(allow_module_level=True)
def test_async_shit():
    bc = AsyncBotController()
    print('\n BotController.clients: ', bc.clients)
    c1 = AbstractClientWindow('c1')
    c2 = AbstractClientWindow('c2')

    bc.add_client(c1)
    bc.add_client(c2)
    print('\n BotController.clients: ', bc.clients)

    async def start_shit():
        await bc.start_bot(c1)
        time.sleep(10)
    asyncio.run(start_shit())

if __name__ == "__main__":
    test_async_shit()