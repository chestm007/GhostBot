from unittest.mock import patch

import GhostBot.controller.async_bot_controller
from GhostBot import logger
from GhostBot.controller.async_bot_controller import AsyncBotController
from GhostBot.controller.bot_controller import BotController, BotClientWindow
from mocks.mock_client import client

import pytest

class MockAsyncBotController(AsyncBotController):
    async def scan_for_clients(self):
        logger.debug("AsyncBotController :: Rescanning clients (uptime %s)", self._total_running_secs)
        await super()._scan_for_clients()
        await self._process_login_queue()


class MockPymem:
    def __init__(self, process_id):
        self.process_id = process_id


@pytest.mark.asyncio
@pytest.mark.usefixtures('monkeypatch', 'client')
async def test_async_shit(monkeypatch, client):
    monkeypatch.setattr(BotClientWindow, 'name', property(lambda self: 'abc'))
    monkeypatch.setattr(BotClientWindow, 'level', property(lambda self: 70))
    with patch('GhostBot.lib.win32.process.PymemProcess.list_clients', new=lambda: [MockPymem(1001)]):
        with patch('GhostBot.controller.bot_controller.BotClientWindow', new=lambda a: client.new_mocked_client()):
            abc = MockAsyncBotController()
            await BotController._scan_for_clients(abc)
            assert 1001 in abc._seen_clients
            #assert 1001 in abc.login_queue.keys()
            assert 'abc' in abc.clients.keys()
