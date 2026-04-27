from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, TypeVar, Self, Generic

import yaml
import time
from GhostBot.lib.utils import retry
from GhostBot.controller.bot_controller import BotClientWindow

from GhostBot.lib.types import Location
from GhostBot.functions import Runner

_T = TypeVar('_T')

class ScriptAction(Enum):
    UNSET = 0
    MOVE = 1
    ATTACK = 2
    WAIT = 3
    LEFT_CLICK = 4
    RIGHT_CLICK = 5
    CONDITIOINAL_LOOP = 6

    @classmethod
    def move(cls, x: int, y: int) -> 'ScriptStep[Location]':
        """Move char to ``location`` and wait until there."""
        return MoveScriptStep(Location(x, y))

    @classmethod
    def attack(cls, target: str) -> 'ScriptStep[str]':
        return AttackScriptStep(target)

    @classmethod
    def wait(cls, timeout: float) -> 'ScriptStep[float]':
        return WaitScriptStep(timeout)

    @classmethod
    def left_click(cls, x: int, y: int) -> 'ScriptStep[Location]':
        return LeftClickScriptStep(Location(x, y))

    @classmethod
    def right_click(cls, x: int, y: int) -> 'ScriptStep[Location]':
        return RightClickScriptStep(Location(x, y))

    @classmethod
    def conditional_loop(cls, actions: list[ScriptStep]) -> 'ScriptStep[list[ScriptStep[_T]]]':
        return ScriptStep[list[ScriptStep[_T]]](actions)


class ScriptStep(Generic[_T], ABC):
    action: ScriptAction = ScriptAction.UNSET

    def __init__(self, parameters: _T):
        self.parameters: _T = parameters

    @abstractmethod
    def execute(self, client: BotClientWindow): ...

class MoveScriptStep(ScriptStep[Location]):
    action = ScriptAction.MOVE

    def execute(self, client: BotClientWindow):
        def _move_and_verify():
            client.move_to_pos(self.parameters)
            return client.location == self.parameters
        return retry(_move_and_verify, 5, delay=0.1)


class AttackScriptStep(ScriptStep[str]):
    action = ScriptAction.ATTACK

    def execute(self, client: BotClientWindow):
        pass


class WaitScriptStep(ScriptStep[float]):
    action = ScriptAction.WAIT
    def execute(self, client: BotClientWindow):
        time.sleep(self.parameters)
        return True


class ClickScriptStep(ScriptStep[Location]):
    def execute(self, client: BotClientWindow):
        if self.action == ScriptAction.LEFT_CLICK:
            client.left_click(self.parameters)
            return True
        elif self.action == ScriptAction.RIGHT_CLICK:
            client.right_click(self.parameters)
            return True
        raise RuntimeError("unknown click action %s", self.action)


class LeftClickScriptStep(ClickScriptStep):
    action = ScriptAction.LEFT_CLICK


class RightClickScriptStep(ClickScriptStep):
    action = ScriptAction.RIGHT_CLICK


class ScriptCondition:
    def __init__(self, condition: Callable[[], bool]):
        self.condition: Callable[[BotClientWindow], bool] = condition

    def __call__(self, client: BotClientWindow) -> bool:
        return self.condition(client)


class ConditionalScriptStep(Generic[_T]):
    def __init__(
            self,
            steps: list[ScriptStep[_T]],
            conditions: list[ScriptCondition],
            handler: ConditionalScriptStepFailedHandler | None = None,
    ):
        self.steps: list[ScriptStep[_T]] = steps
        self.conditions = conditions
        self.handler: ConditionalScriptStepFailedHandler = handler or ConditionalScriptStepFailedHandler.restart


    def execute(self, client: BotClientWindow):
        for step in self.steps:
            step.execute(client)

        if all(c(client) for c in self.conditions):
            return True
        return self.handler()


class ConditionalScriptStepFailedHandler:
    def __init__(self, handler: Callable[[], bool]):
        self.handler: Callable[[], bool] = handler

    def handle(self) -> bool:
        return not self.handler()

    @staticmethod
    def restart():
        False

    @staticmethod
    def ignore():
        True

class ScriptDefinition:
    """
    ..code-block:: yaml

        bc_bot:
        - move: [400, 65]
        - move: [375, 81]
        - move: [354, 111]
        - move: [336, 138]
        - conditional_loop:
          handler: ignore
          conditions:
          - 'client.location == (123, 456)'
          steps:
          - left_click: [400, 65]
          - right_click: [375, 81]

    """
    def __init__(self, *, steps: list[ScriptStep[_T] | ConditionalScriptStep[_T]]):
        self.steps = steps

    @classmethod
    def from_yaml(cls, yaml_file: str) -> Self:
        with open(yaml_file) as f:
            return cls(steps=yaml.safe_load(f))

class Script(Runner):

    def __init__(self, client, script: ScriptDefinition):
        super().__init__(client)
        self.script: ScriptDefinition = script

    def _run(self) -> bool:
        for step in self.script.steps:
            step.execute(self._client)
