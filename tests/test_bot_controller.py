from unittest.mock import MagicMock

import pymem
import pytest
from pymem.ressources.structure import ProcessEntry32

from GhostBot.controller.async_bot_controller import AsyncBotController


to_process = MagicMock(spec=ProcessEntry32)()

@pytest.mark.usefixtures('monkeypatch')
def test_list_clients(monkeypatch):
    monkeypatch.setattr(pymem.process, 'list_processes', lambda: [to_process])
    bot_controller = AsyncBotController()