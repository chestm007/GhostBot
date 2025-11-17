import time

from GhostBot.functions.runner import run_at_interval
from GhostBot.lib.math import seconds
from mocks.mock_client import MockClient


def test_mock_runner_run_at_interval():
    @run_at_interval()
    class MockRunner:
        def __init__(self):
            self.should_exist = True
            self._interval = seconds(seconds=1)
            self._client = MockClient()

        def run(self):
            self.should_exist = not self.should_exist

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
