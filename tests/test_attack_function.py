import time

from GhostBot.functions.attack import AttackContext
from mocks.mock_client import MockClient


def test_attack_context_stuck():
    client = MockClient()
    context = AttackContext(client)

    assert not context.stuck
    client.config.stuck_interval = 2
    print(context._client.config.stuck_interval)
    time.sleep(2.1)
    assert context.stuck  # check that doing nothing for 2.1 secs registers as stuck with an interval of 2 sec

    assert not context.stuck
    client.config.stuck_interval = 1
    client._target_hp = 597
    assert client.target_hp == 100
    time.sleep(1)
    assert context.stuck

    assert not context.stuck
    time.sleep(1)
    client._target_hp -= 10
    assert not context.stuck  # Hp changed, should reset the stuck timer
    time.sleep(0.5)
    assert not context.stuck  # only been 0.5 sec, shouldn't be stuck yet
    time.sleep(0.5)
    assert context.stuck  # more than 1 sec since out last "unstuck", we should be stuck


def test_attack_context_location_check():
    client = MockClient()
    context = AttackContext(client)

    assert not context.location_changed

    client._location = (10, 10)
    assert context.location_changed
    assert not context.location_changed

    client._location = (-10, -10)
    assert context.location_changed
    assert not context.location_changed

    client._location = (-10, -10)
    assert not context.location_changed

    client._location = (0, 0)
    assert context.location_changed
    assert not context.location_changed
