from attrdict import AttrDict

from GhostBot.bot_controller import ExtendedClient, Config


class MockConfig(Config):
    def _detect_path(self):
        return None

    def load(self):
        pass


class MockClient(ExtendedClient):

    def __init__(self):
        self._location = (0, 0)
        self._target_hp = 597

        self.load_config(MockConfig(self))
        self.pointers = AttrDict(
                target_hp=lambda: self._target_hp,
        )

    @property
    def location(self):
        return self._location

