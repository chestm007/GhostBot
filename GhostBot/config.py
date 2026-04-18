from __future__ import annotations

__all__ = [
    'Config',
    'AttackConfig',
    'RegenConfig',
    'FairyConfig',
    'SellConfig',
    'BuffConfig',
    'PetConfig',
    'DeleteConfig',
    'ConfigLoader',
    'LoginDetailsConfigLoader',
    'GhostBotServerConfigLoader',
]

import inspect
import logging
import os
from abc import ABC
from dataclasses import dataclass, field
from typing import TypedDict, NotRequired, Any, TYPE_CHECKING, Sized, TypeVar, Self

import yaml

from GhostBot import logger as _logger
from GhostBot.functions.runner import InjectedLoggingMixin
from GhostBot.lib.utils import subclasses_by_name

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow
    from GhostBot.functions.runner import Runner

_T = TypeVar('_T')

class TypedConfig(ABC):
    logger = _logger.getChild('FunctionConfig')
    @staticmethod
    def _try_change_type(__val, __type: _T) -> _T:
        if __type == bool:
            if isinstance(__val, str):
                if __val.lower() == 'false':
                    return False
            return bool(__val)
        elif __type == tuple[int, int]:
            if isinstance(__val, str):
                __val = __val.split(' ')
            return int(__val[0]), int(__val[1])
        return __type(__val)


    def validate(self):
        def _handle_location(_val):
            if isinstance(_val, str):
                return _val
            if isinstance(_val, set):
                raise TypeError(f'{self.__class__.__name__}.{_attr} is an unexpected type.\n'
                                f'expected {_expected_type}, got {type(_val).__name__}.\n'
                                f'cannot fix as ordering isnt guaranteed in sets.')
            if not len(_val) == 2:
                raise TypeError(f'{self.__class__.__name__}.{_attr} is an unexpected type.\n'
                                f'expected {_expected_type}, got {type(_val).__name__}.\n'
                                f'{_val}')

        for _attr, _expected_type in inspect.get_annotations(type(self),eval_str=True).items():
            def _refresh_val():
                # noinspection PyShadowingNames
                _val = getattr(self, _attr)
                return _val

            def _try_change_type_with_check(check) -> _T:
                if not check(_val):
                    setattr(self, _attr, self._try_change_type(_val, _expected_type))
                    if not check(_refresh_val()):
                        raise TypeError

            _val = _refresh_val()

            if _val is None:
                self.logger.debug(
                    f'{self.__class__.__name__}.{_attr}: [{_expected_type.__name__}] -- value is None in config.')
                continue

            try:
                _try_change_type_with_check(lambda v: isinstance(v, _expected_type))
            except TypeError:
                if isinstance(_val, (Sized, str)) and _expected_type == tuple[int, int]:
                    _handle_location(_val)
                    _try_change_type_with_check(lambda v: (all(map(lambda _v: isinstance(_v, int), v)) and isinstance(v, tuple)))
                elif _attr not in  ('attacks', 'bindings', 'buffs'):
                    raise TypeError(f'{self.__class__.__name__}.{_attr} is an unexpected type.\n'
                                    f'expected {_expected_type}, got {type(_val).__name__}')
                else:
                    self.logger.debug(f'Skipping {self.__class__.__name__}.{_attr}: [{_expected_type.__name__}]')


@dataclass
class FunctionConfig(TypedConfig, ABC):
    pass

@dataclass
class AttackConfig(FunctionConfig):
    class Bindings(TypedDict):
        battle_hp_pot: NotRequired[int | str]
        battle_mana_pot: NotRequired[int | str]
    attacks: list[list[str | int]]
    bindings: Bindings = None
    stuck_interval: int = None
    battle_mana_threshold: float = None
    battle_hp_threshold: float = None
    roam_distance: int = None
    spot: tuple[int, int] = None

@dataclass
class RegenConfig(FunctionConfig):
    class Bindings(TypedDict, total=False):
        hp_pot: NotRequired[int | str]
        mana_pot: NotRequired[int | str]
        sit: NotRequired[int | str]
    bindings: Bindings = field(default_factory=lambda: dict(sit= 'x'))
    hp_threshold: float = None
    mana_threshold: float = None

    def __post_init__(self):
        if self.bindings is None:
            self.bindings = {'sit': "x"}
        elif self.bindings['sit'] is None:
            self.bindings['sit'] = 'x'

@dataclass
class BuffConfig(FunctionConfig):
    buffs: list[list[str | int]]
    interval: int = None

@dataclass
class PetConfig(FunctionConfig):
    class Bindings(TypedDict):
        spawn: NotRequired[int | str]
        food: NotRequired[int | str]
    bindings: Bindings = None
    spawn_interval_mins: int = None
    food_interval_mins: int = None

@dataclass
class FairyConfig(FunctionConfig):
    class Bindings(TypedDict):
        heal: NotRequired[int | str]
        cure: NotRequired[int | str]
        revive: NotRequired[int | str]
    bindings: Bindings = None
    heal_team_threshold: float = None
    heal_self_threshold: float = None

@dataclass
class SellConfig(FunctionConfig):
    class Bindings(TypedDict):
        mount: NotRequired[int | str]
    sell_npc_name: str
    bindings: Bindings = None
    sell_item_pos: int = 1
    sell_interval_mins: int = 60
    npc_search_spot: tuple[int, int] = None
    use_mount: bool = None
    npc_sell_click_spot: tuple[int, int] = None

    def __post_init__(self):
        if self.bindings is None:
            self.bindings = {'mount': 0}

@dataclass
class DeleteConfig(FunctionConfig):
    delete_trash: bool = False
    interval: int = None

@dataclass
class Config:
    attack: AttackConfig = None
    buff: BuffConfig = None
    fairy: FairyConfig = None
    pet: PetConfig = None
    regen: RegenConfig = None
    sell: SellConfig = None
    delete: DeleteConfig = None

    def to_yaml(self) -> dict:
        return {k: v.__dict__ for k, v in self.__dict__.items() if v is not None}

    def validate(self):
        for _name in self._sub_configs_by_name().keys():
            _sub = getattr(self, _name)
            if _sub is not None:
                _sub.validate()

    @staticmethod
    def _sub_configs_by_name() -> dict[str, type[FunctionConfig]]:
        """
        returns a dict of {config_name: FunctionConfig}

        :return: {'attack': <class 'GhostBot.config.AttackConfig'>, ... }
        """
        return {
            clazz.__name__.lower().replace('config', ''): clazz
            for clazz in FunctionConfig.__subclasses__()
        }

    @classmethod
    def load_yaml(cls, data: dict[str, Any]) -> Config:
        _config = cls()
        _confs = cls._sub_configs_by_name()
        for k, v in data.items():
            if (_clazz := _confs.get(k)) is not None:
                setattr(_config, k, _clazz(**{vk: vv for vk, vv in v.items() if v}))
            else:
                raise AttributeError(f"{k} not a valid config category")
        _config.validate()
        return _config

    def functions(self):
        return (k for k, v in self.__dict__.items() if v is not None)


class BaseConfigLoader:
class BaseConfigLoader(ABC):
    config_filename: str

    def __init__(self):
        self.logger = _logger.getChild(self.__class__.__name__)
        self.config_filepath = os.path.join(self._detect_path(), f'{self.config_filename}')

    @staticmethod
    def _detect_path():
        data_path = os.environ.get('HOME', os.environ.get('LOCALAPPDATA'))
        if data_path is None:
            raise FileNotFoundError('what OS u on bro?')

        data_path = os.path.join(data_path, 'GhostBot')
        try:  # make dir if not exist
            os.mkdir(data_path)
        except FileExistsError:
            pass

        return data_path


class ConfigLoader(BaseConfigLoader):
    def __init__(self, client: BotClientWindow):
        self.client = client
        self.config_filename = f'{self.client.name}.yml'
        super().__init__()


    def load(self) -> Config:
        self.logger.debug('ConfigLoader :: %s :: loading config', self.client.identifier)
        try:
            with open(self.config_filepath, 'r') as c:
                _config = Config.load_yaml(yaml.safe_load(c.read()))  # overwrite config defaults with whats in the loaded config
                self.logger.debug('ConfigLoader :: %s :: config loaded', self.client.identifier)
                return _config
        except FileNotFoundError:
            self.logger.debug('ConfigLoader :: %s :: config not found, using defaults', self.client.identifier)
            _config = Config()
            return self.save(_config)

    def save(self, _config: Config) -> Config:
        with open(self.config_filepath, 'w') as c:
            c.write(yaml.safe_dump(_config.to_yaml()))
        return _config


class LoginDetailsConfigLoader(BaseConfigLoader):
    config_filename = 'login_details.yml'

    @dataclass
    class CharDetails:
        char_name: str
        username: str
        password: str
        server: str

    @dataclass
    class LoginDetails:
        chars: dict[str, 'LoginDetailsConfigLoader.CharDetails']

        def items(self):
            return self.chars.items()

    def load(self) -> 'LoginDetailsConfigLoader.LoginDetails':
        """
        reads a config file formatted like

        ::

            char1:
              username: username1
              password: password1
            char2:
              username: username2
              password: password2

        :returns: a dict of ``{char_name: {"username": USERNAME, "password": PASSWORD}}``
        """
        self.logger.debug('loading login config')
        try:
            with open(self.config_filepath, 'r') as c:
                _config: dict[str, dict[str, str]] = yaml.safe_load(c.read())
                self.logger.debug('LoginDetailsConfigLoader :: login config loaded')
                return LoginDetailsConfigLoader.LoginDetails(
                    chars = {
                        _name: LoginDetailsConfigLoader.CharDetails(char_name=_name, **_details)
                        for _name, _details in _config.items()
                    }
                )
        except FileNotFoundError:
            self.logger.debug('LoginDetailsConfigLoader :: no login config file found at %s', self.config_filepath)
            return {}

class GhostBotServerConfigLoader(BaseConfigLoader):
    config_filename = 'ghostbot_server.yml'

    @dataclass
    class GhostBotConfig:
        function_debugging: dict[str, str]

    def __init__(self):
        super().__init__()
        self._config: GhostBotServerConfigLoader.GhostBotConfig | None = None

    def load(self) -> Self:
        try:
            with open(self.config_filepath, 'r') as c:
                _config: dict[str, dict[str, str]] = yaml.safe_load(c.read())
                self.logger.debug('%s :: server config loaded', self.__class__.__name__)
                self._config = GhostBotServerConfigLoader.GhostBotConfig(**_config)

        except FileNotFoundError:
            self.logger.debug('%s :: no server config file found at %s', self.config_filepath, self.__class__.__name__)
            return self

        for k in subclasses_by_name(InjectedLoggingMixin).keys():
            self.logger.info('setting loglevel of [%s] to [%s]', k, logging.INFO)
            logging.getLogger(f'GhostBot.{k}').setLevel(logging.INFO)

        if self._config.function_debugging is None:
            return self
        for k, v in self._config.function_debugging.items():
            self.logger.info('setting loglevel of [%s] to [%s]', k, getattr(logging, v.upper()))
            logging.getLogger(f'GhostBot.{k}').setLevel(getattr(logging, v.upper()))
        return self


if __name__ == "__main__":
    import pprint

    attack_bindings: AttackConfig.Bindings = {'battle_hp_pot': 'F1'}
    fairy_bindings: FairyConfig.Bindings = {'heal': 6}
    pet_bindings: PetConfig.Bindings = {'spawn': 'E', 'food': 9}
    regen_bindings: RegenConfig.Bindings = {'hp_pot': 'Q', 'mana_pot': 'W', 'sit': 'X'}
    config = Config(
        fairy=FairyConfig(
            bindings=fairy_bindings,
            heal_self_threshold=0.75,
        ), attack=AttackConfig(
            bindings=attack_bindings,
            attacks=[
                [1, 1000],
                [2, 1400]
            ]
        ), buff=BuffConfig(
            buffs=[
                [7, 2000]
            ], interval=10
        ), pet=PetConfig(
            bindings=pet_bindings,
            food_interval_mins=55,
        ), regen=RegenConfig(
            bindings=regen_bindings,
        )
    )
    yaml_config = yaml.safe_dump(config.to_yaml())
    assert (processed_config := Config.load_yaml(yaml.safe_load(yaml_config)) == config)
    pprint.pprint(config)

    print("####################")

    for char, details in LoginDetailsConfigLoader().load().items():

        print(char, details)

    print(GhostBotServerConfigLoader().load().apply_function_debugging_levels())

