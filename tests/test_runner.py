import time

import pytest

from GhostBot.controller.bot_controller import BotClientWindow
from GhostBot.functions.runner import run_at_interval
from GhostBot.lib.math import seconds
from mocks.mock_client import MockClient


@pytest.mark.asyncio
@pytest.mark.usefixtures('monkeypatch')
async def test_mock_runner_run_at_interval(monkeypatch):
    @run_at_interval()
    class MockRunner:
        def __init__(self):
            self.should_exist = True
            self._interval = seconds(seconds=1)
            self._client = MockClient()

        async def run(self):
            self.should_exist = not self.should_exist

    monkeypatch.setattr(BotClientWindow, 'in_battle', property(lambda self: False))

    mr = MockRunner()
    assert mr.should_exist
    await mr.run()
    assert mr.should_exist
    time.sleep(mr._interval)
    await mr.run()
    assert not mr.should_exist
    time.sleep(mr._interval)
    await mr.run()
    assert mr.should_exist
