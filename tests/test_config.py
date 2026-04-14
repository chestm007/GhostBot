import pickle

from GhostBot import logger
from GhostBot.config import AttackConfig, RegenConfig, BuffConfig, PetConfig, FairyConfig, Config, SellConfig
from GhostBot.rpc.message import Message
from GhostBot.server import IPCClient, GhostbotIPCServer

def _config():
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
            sit="y",
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

    return Config(
        attack=ac,
        buff=bc,
        fairy=fc,
        pet=pc,
        regen=rc,
    )


def test_config_constructors():
    config = _config()
    assert Config.load_yaml(config.to_yaml()) == config

def test_config_ipc():
    config = _config()
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

def test_config_none_not_stringified():
    config = Config(
        attack=AttackConfig(attacks=[[1, 1000]], bindings=dict(battle_hp_pot="F1", battle_mp_pot="F2"))
    ).to_yaml()
    for _name, _conf in config.items():
        logger.debug(_conf)
        assert all(b != 'None' for b in _conf.get('bindings').values() if _conf.get('bindings') is not None)


def test_config_loads_yaml_and_parses_types_properly():
    attack_bindings: AttackConfig.Bindings = {'battle_hp_pot': 'F1'}
    fairy_bindings: FairyConfig.Bindings = {'heal': 6}
    pet_bindings: PetConfig.Bindings = {'spawn': 'E', 'food': 9}
    regen_bindings: RegenConfig.Bindings = {'hp_pot': 'Q', 'mana_pot': 'W', 'sit': 'X'}

    # We're deliberately passing the wrong types in here to ensure they're converted later.
    # noinspection PyTypeChecker
    config = Config(
        fairy=FairyConfig(
            bindings=fairy_bindings,
            heal_self_threshold='0.75',
            heal_team_threshold='0.5',
        ), attack=AttackConfig(
            bindings=attack_bindings,
            attacks=[
                [1, 1000],
                [2, 1400]
            ],
            stuck_interval='4',
            battle_mana_threshold='0.56',
            battle_hp_threshold=0.75,
            roam_distance='40'
        ), buff=BuffConfig(
            buffs=[
                [7, 2000]
            ],
            interval='10'
        ), pet=PetConfig(
            bindings=pet_bindings,
            food_interval_mins=55,
            spawn_interval_mins='55',
        ), regen=RegenConfig(
            bindings=regen_bindings,
            hp_threshold='0.75',
            mana_threshold=0.75,
            spot=(123, '456'),
        ), sell=SellConfig(
            sell_npc_name='Mr Guy Man',
            use_mount='false',
            npc_sell_click_spot=(100, 200),
            npc_search_spot=['123', 456],
            return_spot=[123, '456'],
        ),
    )

    config.validate()
    assert isinstance(config.fairy.heal_self_threshold, float)
    assert isinstance(config.attack.battle_mana_threshold, float)
    assert not config.sell.use_mount
    assert isinstance(config.buff.interval, int)
    assert config.regen.spot == (123, 456)
    assert config.sell.npc_sell_click_spot == (100, 200)

def test_config_validation():
    pass