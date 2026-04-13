import os

import pytest
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
