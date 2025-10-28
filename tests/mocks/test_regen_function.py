import pytest

from GhostBot.config import Config, RegenConfig
from GhostBot.functions.regen import Regen
from mocks.mock_client import MockClient

config = Config(
    regen=RegenConfig(bindings={'sit': 'X', 'hp_pot': 'Q', 'mana_pot': 'W'})
)

client = MockClient()
client.config = config


def test_regen_doesnt_trigger_when_hp_full():
    regen = Regen(client)
    assert not regen.run()

def test_regen_trigger_when_hp_50_pct():
    client._hp = 0.1
    client.config.hp_threshold = 0.75
    client.config.mana_threshold = 0.75
    client.config.bindings = dict(hp_pot=4)

    regen = Regen(client)
    Regen._use_hp_pot = lambda self: setattr(client, '_hp', 100)
    assert regen.run()

def test_regen_breaks_out_when_attacked():
    client._hp = 0.1
    client.config.hp_threshold = 0.75
    client.config.mana_threshold = 0.75

    regen = Regen(client)
    Regen._use_hp_pot = lambda self: setattr(client, '_in_battle', True)
    assert not regen.run()

