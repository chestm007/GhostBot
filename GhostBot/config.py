from __future__ import annotations

import os
import pprint
from abc import ABC
from dataclasses import dataclass, field
from typing import TypedDict, NotRequired, Any

import yaml

from GhostBot import logger


class FunctionConfig(ABC):
    pass

@dataclass
class AttackConfig(FunctionConfig):
    class Bindings(TypedDict):
        battle_hp_pot: NotRequired[int | str]
        battle_mana_pot: NotRequired[int | str]
    attacks: list[list[str | int]]
    bindings: Bindings | None = None
    stuck_interval: int | None = None
    battle_mana_threshold: float | None = None
    battle_hp_threshold: float | None = None
    roam_distance: int | None = None

@dataclass
class RegenConfig(FunctionConfig):
    class Bindings(TypedDict):
        hp_pot: NotRequired[int | str]
        mana_pot: NotRequired[int | str]
        sit: NotRequired[int | str]
    bindings: Bindings | None = field(default_factory=lambda: {'sit': 'x'})
    hp_threshold: float | None = None
    mana_threshold: float | None = None
    spot: list[int] = None

    def __post_init__(self):
        if self.bindings is None:
            self.bindings = {'sit': "x"}
        elif self.bindings['sit'] is None:
            self.bindings['sit'] = 'x'

@dataclass
class BuffConfig(FunctionConfig):
    buffs: list[list[str | int]]
    interval: int | None = None

@dataclass
class PetConfig(FunctionConfig):
    class Bindings(TypedDict):
        spawn: NotRequired[int | str]
        food: NotRequired[int | str]
    bindings: Bindings = None
    spawn_interval_mins: int | None = None
    food_interval_mins: int | None = None

@dataclass
class FairyConfig(FunctionConfig):
    class Bindings(TypedDict):
        heal: NotRequired[int | str]
        cure: NotRequired[int | str]
        revive: NotRequired[int | str]
    bindings: Bindings = None
    heal_team_threshold: float | None = None
    heal_self_threshold: float | None = None

@dataclass
class SellConfig(FunctionConfig):
    class Bindings(TypedDict):
        mount: NotRequired[int | str]
    sell_npc_name: str
    bindings: Bindings = None
    sell_item_pos: int = 1
    sell_interval_mins: int = 60
    npc_search_spot: list[int] | None = None
    return_spot: list[int] | None = None
    use_mount: bool | None = None

    def __post_init__(self):
        if self.bindings is None:
            self.bindings = {'mount': 0}

@dataclass
class DeleteConfig(FunctionConfig):
    delete_trash: bool = False

@dataclass
class Config:
    attack: AttackConfig | None = None
    buff: BuffConfig | None = None
    fairy: FairyConfig = None
    pet: PetConfig | None = None
    regen: RegenConfig | None = None
    sell: SellConfig | None = None
    delete: DeleteConfig | None = None

    def to_yaml(self) -> dict:
        return {k: v.__dict__ for k, v in self.__dict__.items() if v is not None}

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
                setattr(_config, k, _clazz(**v))
            else:
                raise AttributeError(f"{k} not a valid config category")

        logger.debug(f"Config loaded: {data.keys()}")
        return _config

    def functions(self):
        return (k for k, v in self.__dict__.items() if v is not None)


class ConfigLoader:
    def __init__(self, client):
        self.client = client
        self.config_filepath = self._detect_path()

    def _detect_path(self):
        char_name = self.client.name
        data_path = os.environ.get('HOME', os.environ.get('LOCALAPPDATA'))
        if data_path is None:
            raise FileNotFoundError('what OS u on bro?')

        data_path = os.path.join(data_path, 'GhostBot')
        try:  # make dir if not exist
            os.mkdir(data_path)
        except FileExistsError:
            pass

        return os.path.join(data_path, f'{char_name}.yml')

    def load(self) -> Config:
        logger.debug('loading config')
        try:
            with open(self.config_filepath, 'r') as c:
                _config = Config.load_yaml(yaml.safe_load(c.read()))  # overwrite config defaults with whats in the loaded config
                logger.debug('config loaded')
                return _config
        except FileNotFoundError:
            logger.debug('config not found, using defaults')
            _config = Config()
            return self.save(_config)


    def save(self, _config: Config) -> Config:
        with open(self.config_filepath, 'w') as c:
            c.write(yaml.safe_dump(_config.to_yaml()))
        return _config


if __name__ == "__main__":
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

