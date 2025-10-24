from attrdict import AttrDict

from GhostBot.bot_controller import ExtendedClient
from GhostBot.config import Config


class MockConfig(Config):
    def _detect_path(self):
        return None

    def load(self):
        pass


class MockClient(ExtendedClient):

    def __init__(self):
        self._name = "testChar"
        self._location = (0, 0)
        self._target_hp = 597
        self._is_target_selected = True
        self._in_battle = False
        self._sitting = False

        self._mana = 100
        self._max_mana = 100

        self._hp = 100
        self._max_hp = 100


        self.config = MockConfig(self)
        self.pointers = AttrDict(
            target_hp=lambda: self._target_hp,
            is_target_selected=lambda: self._is_target_selected,
            get_mana=lambda: self._mana,
            get_max_mana=lambda: self._max_mana,
            get_hp=lambda: self._hp,
            get_max_hp=lambda: self._max_hp,
            is_in_battle=lambda: self._in_battle,
            is_sitting=lambda: self._sitting,
        )

    @property
    def location(self):
        return self._location

    def press_key(self, key: str):
        print("press key", key)

