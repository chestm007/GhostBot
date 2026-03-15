import pytest

from GhostBot.config import Config, RegenConfig
from GhostBot.enums.bot_status import BotStatus
from GhostBot.functions.regen import Regen
from mocks.mock_client import MockClient

config = Config(
    regen=RegenConfig(bindings=dict(sit='X', hp_pot='Q', mana_pot='W'))
)

client = MockClient()
client.config = config


def test_regen_doesnt_trigger_when_hp_full():
    regen = Regen(client)
    client.bot_status = BotStatus.running
    assert not regen.run()

def test_regen_not_trigger_when_hp_over_thresh():
    client._hp = 76
    client._mana = 100
    client.config.hp_threshold = 0.75
    client.config.mana_threshold = 0.75
    client.config.bindings = dict(hp_pot=4)

    regen = Regen(client)
    Regen._use_hp_pot = lambda self: setattr(client, '_hp', 100)
    client.bot_status = BotStatus.running
    assert not regen.run()

def test_regen_trigger_when_hp_50_pct():
    client._hp = 0.1
    client._mana = 100
    client.config.hp_threshold = 0.75
    client.config.mana_threshold = 0.75
    client.config.bindings = dict(hp_pot=4)

    regen = Regen(client)
    Regen._use_hp_pot = lambda self: setattr(client, '_hp', 100)
    client.bot_status = BotStatus.running
    assert regen.run()

def test_regen_trigger_when_mana_50_pct():
    client._mana = 0.1
    client.config.mana_threshold = 0.75
    client.config.mana_threshold = 0.75
    client.config.bindings = dict(mana_pot=4)

    regen = Regen(client)
    Regen._use_mana_pot = lambda self: setattr(client, '_hp', 100)
    client.bot_status = BotStatus.running
    assert regen.run()

def test_regen_breaks_out_when_attacked():
    client._hp = 0.1
    client.config.hp_threshold = 0.75
    client.config.mana_threshold = 0.75

    regen = Regen(client)
    Regen._use_hp_pot = lambda self: setattr(client, '_in_battle', True)
    client.bot_status = BotStatus.running
    client.running = True
    assert not regen.run()

