from types import coroutine

import pytest

from GhostBot import logger
from GhostBot.abstract_client_window import Location
from GhostBot.controller.bot_controller import BotClientWindow
from GhostBot.enums.bot_status import BotStatus
from GhostBot.functions.regen import Regen
from mocks.mock_client import client

logger.debug = print
logger.setLevel(10)

@pytest.mark.asyncio
@pytest.mark.usefixtures('client', 'monkeypatch')
async def test_regen_doesnt_trigger_when_hp_full(client, monkeypatch):
    monkeypatch.setattr(BotClientWindow, 'mana', property(lambda self: 100))
    monkeypatch.setattr(BotClientWindow, 'hp', property(lambda self: 100))

    regen = Regen(client)
    client.bot_status = BotStatus.running
    assert not await regen.run()

@pytest.mark.asyncio
@pytest.mark.usefixtures('client', 'monkeypatch')
async def test_regen_not_trigger_when_hp_over_thresh(client, monkeypatch):
    _hp = 76
    monkeypatch.setattr(BotClientWindow, 'mana', property(lambda self: 100))
    monkeypatch.setattr(BotClientWindow, 'hp', property(lambda self: _hp))

    client.config.hp_threshold = 0.75
    client.config.mana_threshold = 0.75
    client.config.bindings = dict(hp_pot=4)

    regen = Regen(client)
    Regen._use_hp_pot = lambda self: _hp.__eq__(100)
    client.bot_status = BotStatus.running
    assert not await regen.run()

@pytest.mark.asyncio
@pytest.mark.usefixtures('client', 'monkeypatch')
async def test_regen_trigger_when_hp_50_pct(client, monkeypatch):
    _hp = 0.1
    monkeypatch.setattr(BotClientWindow, 'mana', property(lambda self: 100))
    monkeypatch.setattr(BotClientWindow, 'hp', property(lambda self: _hp))
    monkeypatch.setattr(BotClientWindow, 'location', Location(200, 200))
    monkeypatch.setattr(BotClientWindow, 'in_battle', False)

    client.config.hp_threshold = 0.75
    client.config.mana_threshold = 0.75
    client.config.bindings = dict(hp_pot=4)

    regen = Regen(client)
    async def _set_hp(self):
        _hp.__eq__(100)
    Regen._use_hp_pot = _set_hp
    client.bot_status = BotStatus.running
    assert await regen.run()

@pytest.mark.asyncio
@pytest.mark.usefixtures('client', 'monkeypatch')
async def test_regen_trigger_when_mana_50_pct(client, monkeypatch):
    _mana = 0.1
    monkeypatch.setattr(BotClientWindow, 'mana', property(lambda self: _mana))
    monkeypatch.setattr(BotClientWindow, 'hp', property(lambda self: 100))
    monkeypatch.setattr(BotClientWindow, 'location', Location(200, 200))
    monkeypatch.setattr(BotClientWindow, 'in_battle', False)

    client.config.mana_threshold = 0.75
    client.config.mana_threshold = 0.75
    client.config.bindings = dict(mana_pot=4)

    regen = Regen(client)
    async def _set_mp(self):
        _mana.__eq__(100)
    Regen._use_mana_pot = _set_mp
    client.bot_status = BotStatus.running
    assert await regen.run()

@pytest.mark.asyncio
@pytest.mark.usefixtures('client', 'monkeypatch')
async def test_regen_breaks_out_when_attacked(client, monkeypatch):
    monkeypatch.setattr(BotClientWindow, 'mana', property(lambda self: 100))
    monkeypatch.setattr(BotClientWindow, 'hp', property(lambda self: 0.1))
    monkeypatch.setattr(BotClientWindow, 'location', Location(200, 200))
    monkeypatch.setattr(BotClientWindow, 'in_battle', False)

    client.config.hp_threshold = 0.75
    client.config.mana_threshold = 0.75

    regen = Regen(client)

    async def _set_battle(self):
        monkeypatch.setattr(BotClientWindow, 'in_battle', True)

    Regen._use_hp_pot = _set_battle
    client.bot_status = BotStatus.running
    client.running = True
    assert not await regen.run()

