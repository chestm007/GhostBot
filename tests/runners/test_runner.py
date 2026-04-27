import time

import pytest

from GhostBot.controller.bot_controller import BotClientWindow
from GhostBot.functions.runner import run_at_interval
from GhostBot.lib.math import seconds
from mocks.mock_client import MockClient


@pytest.mark.usefixtures('monkeypatch')
def test_mock_runner_run_at_interval(monkeypatch):
    @run_at_interval()
    class MockRunner:
        def __init__(self):
            self.should_exist = True
            self._interval = seconds(seconds=1)
            self._client = MockClient()

        def run(self):
            self.should_exist = not self.should_exist

        def _log_debug(self, msg, *args):
            print(msg % args)

    monkeypatch.setattr(BotClientWindow, 'in_battle', property(lambda self: False))

    mr = MockRunner()
    assert mr.should_exist
    mr.run()
    assert mr.should_exist
    time.sleep(mr._interval)
    mr.run()
    assert not mr.should_exist
    time.sleep(mr._interval)
    mr.run()
    assert mr.should_exist
