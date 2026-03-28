from unittest.mock import MagicMock, patch

import pymem
import pytest

from GhostBot.controller.bot_controller import BotClientWindow
from GhostBot.config import Config, AttackConfig, RegenConfig


class MockConfig(Config):
    def _detect_path(self):
        return None

    def load(self):
        pass


def MockClient() -> BotClientWindow:
    with patch('GhostBot.client_window.Pointers', spec_set=True):
        with patch('GhostBot.controller.bot_controller.ConfigLoader', spec_set=True):
            bcw = BotClientWindow
            mocked = bcw(MagicMock(spec=pymem.Pymem)())
            mocked.pointers.get_max_mana = lambda: 100
            mocked.pointers.get_max_hp = lambda: 100
            return mocked


@pytest.fixture
def client():
    config = Config(
        attack=AttackConfig(attacks=None),
        regen=RegenConfig(bindings=dict(sit='X', hp_pot='Q', mana_pot='W'))
    )
    client = MockClient()
    client.config = config
    return client
