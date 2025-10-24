import pickle

from GhostBot.config import AttackConfig, RegenConfig, BuffConfig, PetConfig, FairyConfig, Config
from GhostBot.rpc.message import Message
from GhostBot.server import IPCClient, GhostbotIPCServer


def test_config_constructors():
    ac = AttackConfig(
        attacks=[
            [1, 1000],
            [2, 2000],
            [3, 3000],
        ],
        bindings=dict(
            battle_hp_pot="F2",
            battle_mana_pot="F3"
        ),
        stuck_interval=10,
        battle_mana_threshold=12,
        battle_hp_threshold=13,
        roam_distance=20
    )

    rc = RegenConfig(
        bindings=dict(
            hp_pot="q",
            mana_pot="w",
            sit="y"
        ),
        hp_threshold=10,
        mana_threshold=12,
        spot=(123, 456)
    )

    bc = BuffConfig(
        buffs=[
            [8, 1000],
            [9, 2000],
        ],
        interval=10,
    )

    pc = PetConfig(
        bindings=dict(
            spawn="f",
            food=9
        ),
        spawn_interval_mins=20,
        food_interval_mins=60
    )

    fc = FairyConfig(
        bindings=dict(
            heal=6,
            revive=8,
        ),
        heal_team_threshold=0.6,
        heal_self_threshold=None
    )

    config = Config(
        attack=ac,
        buff=bc,
        fairy=fc,
        pet=pc,
        regen=rc,
    )

    assert Config.load_yaml(config.to_yaml()) == config

def test_config_ipc():
    ac = AttackConfig(
        attacks=[
            [1, 1000],
            [2, 2000],
            [3, 3000],
        ],
        bindings=dict(
            battle_hp_pot="F2",
            battle_mana_pot="F3"
        ),
        stuck_interval=10,
        battle_mana_threshold=12,
        battle_hp_threshold=13,
        roam_distance=20
    )

    rc = RegenConfig(
        bindings=dict(
            hp_pot="q",
            mana_pot="w",
            sit="y"
        ),
        hp_threshold=10,
        mana_threshold=12,
        spot=(123, 456)
    )

    bc = BuffConfig(
        buffs=[
            [8, 1000],
            [9, 2000],
        ],
        interval=10,
    )

    pc = PetConfig(
        bindings=dict(
            spawn="f",
            food=9
        ),
        spawn_interval_mins=20,
        food_interval_mins=60
    )

    fc = FairyConfig(
        bindings=dict(
            heal=6,
            revive=8,
        ),
        heal_team_threshold=0.6,
        heal_self_threshold=None
    )

    config = Config(
        attack=ac,
        buff=bc,
        fairy=fc,
        pet=pc,
        regen=rc,
    )

    class DummyBC:
        _client = None
        def get_client(self, client):
            pass

    class TestIPCClient(IPCClient):
        def send(self, data: Message) -> Message:
            return pickle.loads(pickle.dumps(data))

    class TestGhostbotIPCServer(GhostbotIPCServer):
        def __init(self, bot_controller: DummyBC):
            self.bot_controller = bot_controller

        def listen(self):
            pass

    client = TestIPCClient()
    #server = GhostbotIPCServer(DummyBC())

    assert Config.load_yaml(client.set_config('test_client', config).target.get('config')) == config


