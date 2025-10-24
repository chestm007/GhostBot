from __future__ import annotations

import os
import pprint
from abc import ABC
from dataclasses import dataclass, field
from typing import TypedDict, NotRequired

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

@dataclass
class BuffConfig(FunctionConfig):
    buffs: list[list[str | int]]
    interval: int | None = None

@dataclass
class PetConfig(FunctionConfig):
    class Bindings(TypedDict):
        spawn: NotRequired[int | str]
        food: NotRequired[int | str]
    bindings: Bindings | None = None
    spawn_interval_mins: int | None = None
    food_interval_mins: int | None = None

@dataclass
class FairyConfig(FunctionConfig):
    class Bindings(TypedDict):
        heal: NotRequired[int | str]
        cure: NotRequired[int | str]
        revive: NotRequired[int | str]
    bindings: Bindings | None = None
    heal_team_threshold: float | None = None
    heal_self_threshold: float | None = None

@dataclass
class Config:
    attack: AttackConfig | None = None
    buff: BuffConfig | None = None
    fairy: FairyConfig = None
    pet: PetConfig | None = None
    regen: RegenConfig | None = None

    def to_yaml(self) -> dict:
        return {k: v.__dict__ for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def load_yaml(cls, data: dict) -> Config:
        _config = cls()
        for k, v in data.items():
            match k:
                case 'attack': _config.attack = AttackConfig(**v)
                case 'buff': _config.buff = BuffConfig(**v)
                case 'pet': _config.pet = PetConfig(**v)
                case 'fairy': _config.fairy = FairyConfig(**v)
                case 'regen': _config.regen = RegenConfig(**v)
                case _: raise AttributeError(f"{k} not a valid config category")
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

