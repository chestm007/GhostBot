from unittest.mock import MagicMock

import pytest

from GhostBot.controller.bot_controller import BotClientWindow
from mocks.mock_client import MockClient


@pytest.mark.usefixtures('monkeypatch')
def test_key_pressers(monkeypatch):
        monkeypatch.setattr(BotClientWindow, 'press_key', MagicMock())
        client = MockClient()
        client.new_target()
        client.press_key.assert_called_once()
        client.press_key.assert_called_with('tab')