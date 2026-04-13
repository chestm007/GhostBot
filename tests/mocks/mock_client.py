import os
import pathlib
from unittest.mock import MagicMock, patch

import cv2
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
            class MockClientWindow(BotClientWindow):
                _path_base = pathlib.Path(__file__).resolve().parent.parent
                _image = None

                def capture_window(self, color=False):
                    print('capture window called')
                    assert self._image is not None
                    if not os.path.isfile(self._image):
                        raise FileNotFoundError(self._image)
                    return cv2.imread(self._image, cv2.IMREAD_GRAYSCALE)

                @classmethod
                def new_mocked_client(cls):
                    mocked = cls(MagicMock(spec=pymem.Pymem)())
                    return mocked

                def initialize_pointers(self, force_reload: bool = False):
                    class Pointers:
                        get_max_mana = lambda _: 100
                        get_max_hp = lambda _: 100
                        get_dc = lambda _: False
                        get_x = lambda _: 0
                        get_y = lambda _: 0
                        mount = lambda _: None
                        is_bag_open = lambda _: None
                    self.pointers = Pointers()

            return MockClientWindow.new_mocked_client()


@pytest.fixture
def client():
    config = Config(
        attack=AttackConfig(attacks=None),
        regen=RegenConfig(bindings=dict(sit='X', hp_pot='Q', mana_pot='W'))
    )
    client = MockClient()
    client.config = config
    return client
