import os.path
import pathlib
from unittest.mock import MagicMock, AsyncMock

import cv2
import pytest
from mocks.mock_client import client

from GhostBot.client_window import Win32ClientWindow
from GhostBot.image_finder import ImageFinder


class MockClientWindow(Win32ClientWindow):
    _path_base = pathlib.Path(__file__).resolve().parent
    _image = os.path.join(_path_base, "images", 'inventory.bmp')

    def __init__(self, *args, **kwargs):
        pass

    def capture_window(self, color=False):
        return cv2.imread(self._image, cv2.IMREAD_GRAYSCALE)


def test_image_finder_get_destroy_item_location():
    image_finder = ImageFinder(MockClientWindow())
    assert image_finder._get_destroy_item_location()


@pytest.mark.asyncio
@pytest.mark.usefixtures('monkeypatch', 'client')
async def test_mounted_context_manager(monkeypatch, client):
    _calls = []
    async def call(_call):
        _calls.append(_call)
    monkeypatch.setattr(client, 'mount', lambda _key: call(f'mount-{_key}'))
    monkeypatch.setattr(client, 'dismount', lambda _key: call(f'dismount-{_key}'))

    _on_mount = False
    monkeypatch.setattr(client.pointers, 'mount', lambda: _on_mount)
    async with client.mounted(_key="F1"):
        assert _calls == ["mount-F1"]
    assert _calls == ["mount-F1", "dismount-F1"]


@pytest.mark.asyncio
@pytest.mark.usefixtures('monkeypatch', 'client')
async def test_inventory_context_manager(monkeypatch, client):
    _calls = []
    async def call(_call):
        _calls.append(_call)
    monkeypatch.setattr(client, 'open_inventory', lambda : call(f'open_inventory'))
    monkeypatch.setattr(client, 'close_inventory', lambda : call(f'close_inventory'))

    _bag_open = False
    monkeypatch.setattr(client.pointers, 'is_bag_open', lambda: _bag_open)
    async with client.inventory():
        assert _calls == ["open_inventory"]
    assert _calls == ["open_inventory", "close_inventory"]
