from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, TypeVar, Self, Generic

import yaml

from GhostBot.lib.types import Location
from GhostBot.functions import Runner

if TYPE_CHECKING:
    pass

_T = TypeVar('_T')

class ScriptAction(Enum):
    MOVE = 1
    ATTACK = 2

    def move(self, location: Location):
        """Move char to ``location`` and wait until there."""
        return ScriptStep[Location](self.MOVE, location)

    def attack(self, target: str):
        return ScriptStep[str](self.ATTACK, target)

@dataclass
class ScriptStep(Generic[_T]):
    action: ScriptAction
    parameters: _T

class ScriptDefinition:
    """
    ..code-block:: yaml

        bc_bot:
        - move [400, 65]
        - move [375, 81]
        - move [354, 111]
        - move [336, 138]

    """
    def __init__(self, *, steps: list[ScriptStep[_T]]):
        self.steps = steps

    @classmethod
    def from_yaml(cls, yaml_file: str) -> Self:
        with open(yaml_file) as f:
            return cls(steps=yaml.safe_load(f))

class Script(Runner):

    def _run(self) -> bool:
        pass