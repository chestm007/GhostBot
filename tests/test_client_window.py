import os

import pytest

from GhostBot.functions.script import ScriptCondition
from GhostBot.map_navigation import zone_to_capwords, location_to_zone_map, location_to_zone_map_capwords

from GhostBot.controller.threaded_bot_controller import ThreadedBotController

from mocks.mock_client import client

from GhostBot.image_finder import ImageFinder


@pytest.mark.usefixtures('client')
def test_image_finder_get_destroy_item_location(client):
    client._image = os.path.join(client._path_base, "images", 'inventory.bmp')
    image_finder = ImageFinder(client)
    assert image_finder._get_destroy_item_location()


@pytest.mark.usefixtures('monkeypatch', 'client')
def test_mounted_context_manager(monkeypatch, client):
    _calls = []
    def call(_call):
        _calls.append(_call)
    monkeypatch.setattr(client, 'mount', lambda _key: call(f'mount-{_key}'))
    monkeypatch.setattr(client, 'dismount', lambda _key: call(f'dismount-{_key}'))

    _on_mount = False
    monkeypatch.setattr(client.pointers, 'mount', lambda: _on_mount)
    with client.mounted(_key="F1"):
        assert _calls == ["mount-F1"]
    assert _calls == ["mount-F1", "dismount-F1"]


@pytest.mark.usefixtures('monkeypatch', 'client')
def test_inventory_context_manager(monkeypatch, client):
    _calls = []
    def call(_call):
        _calls.append(_call)
    monkeypatch.setattr(client, 'open_inventory', lambda : call(f'open_inventory'))
    monkeypatch.setattr(client, 'close_inventory', lambda : call(f'close_inventory'))

    _bag_open = False
    monkeypatch.setattr(client.pointers, 'is_bag_open', lambda: _bag_open)
    with client.inventory():
        assert _calls == ["open_inventory"]
    assert _calls == ["open_inventory", "close_inventory"]

@pytest.mark.skip("local testing only for now")
def test_team_members():
    bc = ThreadedBotController()
    bc._running = True
    bc._scan_for_clients()
    wyp = bc.clients.get('bot_name')
    print(wyp.team_size)
    assert not [t.team_members[0].name for t in wyp.team_members]

@pytest.mark.skip("local testing only for now")
def test_char_location():
    bc = ThreadedBotController()
    bc._running = True
    bc._scan_for_clients()
    wyp = bc.clients.get('bot_name')
    assert location_to_zone_map_capwords(wyp.location_name) == 'Stone City'

    _cond = ScriptCondition.client_location_name('Stone City', match=True)
    assert _cond(wyp)

    _cond2 = ScriptCondition.client_location_name("Dai's Field", match=True)
    assert not _cond2(wyp)

    _cond3 = ScriptCondition.client_location_name('Stone City', match=False)
    assert not _cond3(wyp)

    _cond3 = ScriptCondition.client_location_name("Dai's Field", match=False)
    assert _cond3(wyp)
