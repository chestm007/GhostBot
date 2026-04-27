import time

import pytest

from GhostBot.abstract_client_window import Location
from GhostBot.controller.bot_controller import BotClientWindow
from GhostBot.functions.attack import AttackContext
from mocks.mock_client import client


@pytest.mark.usefixtures('monkeypatch', 'client')
def test_attack_context_stuck(monkeypatch, client):
    _target_hp = 100
    monkeypatch.setattr(BotClientWindow, 'target_hp', property(lambda self: _target_hp))
    monkeypatch.setattr(BotClientWindow, 'location', Location(200, 200))
    context = AttackContext(client, 2)

    assert not context.stuck
    context._stuck_interval = 2
    time.sleep(2.1)
    assert context.stuck  # check that doing nothing for 2.1 secs registers as stuck with an interval of 2 sec

    assert not context.stuck
    context._stuck_interval = 1
    _target_hp = 100
    assert client.target_hp == 100
    time.sleep(1.0)
    assert context.stuck

    assert not context.stuck
    time.sleep(1)
    _target_hp -= 10
    assert not context.stuck  # Hp changed, should reset the stuck timer
    time.sleep(0.5)
    assert not context.stuck  # only been 0.5 sec, shouldn't be stuck yet
    time.sleep(0.5)
    assert context.stuck  # more than 1 sec since out last "unstuck", we should be stuck


@pytest.mark.usefixtures('monkeypatch', 'client')
def test_attack_context_location_check(monkeypatch, client):
    _target_hp = 100
    _location = Location(200, 200)
    monkeypatch.setattr(BotClientWindow, 'target_hp', property(lambda self: _target_hp))
    monkeypatch.setattr(BotClientWindow, 'location', property(lambda self: _location))
    context = AttackContext(client, 2)

    assert not context.location_changed

    _location = Location(10, 10)
    assert context.location_changed
    assert not context.location_changed

    _location = Location(-10, -10)
    assert context.location_changed
    assert not context.location_changed

    _location = Location(-10, -10)
    assert not context.location_changed

    _location = Location(0, 0)
    assert context.location_changed
    assert not context.location_changed
