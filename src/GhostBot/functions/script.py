from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TypeVar, Self, Generic, Callable, Iterable, TYPE_CHECKING

import yaml
import time

from GhostBot import logger

from GhostBot.lib.talisman_ui_locations import UI_locations

from GhostBot.lib.utils import retry

from GhostBot.lib.types import Location
from GhostBot.functions import Runner
from GhostBot.map_navigation import location_to_zone_map_capwords

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotClientWindow

_T = TypeVar('_T')


class ScriptAction(Enum):
    UNSET = 0
    MOVE = 1
    ATTACK = 2
    WAIT = 3
    LEFT_CLICK = 4
    RIGHT_CLICK = 5
    CONDITIONAL_LOOP = 6
    LOOP = 7

    @classmethod
    def from_yaml(cls, step):
        if isinstance(step, str):
            return cls._from_yaml(step)
        elif isinstance(step, dict):
            step, step_cfg = step.popitem()
            return cls._from_yaml(step, step_cfg)
        elif isinstance(step, ScriptStep):
            return step
        else:
            raise TypeError('step must be str, dict, or ScriptStep %s', step)

    @classmethod
    def _from_yaml(cls, _name, params = None):
        if _name in ('move', 'left_click', 'right_click'):
            x, y = params.split(' ')
            params = (int(x), int(y))
        if isinstance(params, dict):
            return getattr(cls, _name)(**params)
        if isinstance(params, Iterable):
            return getattr(cls, _name)(*params)
        elif params is None:
            return getattr(cls, _name)()
        return getattr(cls, _name)(params)

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
    def goto_npc(cls, npc_name: str) -> 'ScriptStep[str]':
        return GotoNPC(npc_name)

    @classmethod
    def click_npc(cls) -> ScriptStep[Location]:
        return RightClickScriptStep(UI_locations.npc_location)

    @classmethod
    def select_npc(cls) -> ScriptStep[Location]:
        return SelectNPCScriptStep(UI_locations.npc_location)

    @classmethod
    def left_click(cls, x: int, y: int) -> 'ScriptStep[Location]':
        return LeftClickScriptStep(Location(x, y))

    @classmethod
    def right_click(cls, x: int, y: int) -> 'ScriptStep[Location]':
        return RightClickScriptStep(Location(x, y))

    @classmethod
    def loop(cls, count: int, steps: list[ScriptStep[_T]]) -> LoopScriptStep[_T]:
        return LoopScriptStep(count, steps)

    @classmethod
    def conditional_loop(
            cls,
            steps: list[ScriptStep[_T]] | str | dict,
            conditions: list[ScriptCondition] | None = None,
            pre_conditions: list[ScriptCondition] | None = None,
            handler: ConditionalScriptStepFailedHandler | None = None,
    ) -> ConditionalScriptStep:
        return ConditionalScriptStep(
            steps=steps,
            conditions=conditions,
            pre_conditions=pre_conditions,
            handler=handler,
        )


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


class GotoNPC(ScriptStep[str]):
    action = ScriptAction.MOVE
    def execute(self, client: BotClientWindow):
        client.search_surroundings(self.parameters)
        client.goto_first_surrounding_result()
        client.block_while_moving()


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


class SelectNPCScriptStep(RightClickScriptStep):
    def execute(self, client: BotClientWindow):
        def _select_npc_and_verify() -> bool:
            client.right_click(self.parameters)
            return client.target_name is not None
        return retry(_select_npc_and_verify, 10, 2)


class LoopScriptStep(ScriptStep[_T]):
    action = ScriptAction.LOOP
    def __init__(self, count: int, steps: list[ScriptStep]):
        super().__init__(count)
        self.steps: list[ScriptStep[_T]] = []
        for step in steps:
            self.steps.append(ScriptAction.from_yaml(step))

    def execute(self, client: BotClientWindow):
        for i in range(self.parameters):
            for step in self.steps:
                step.execute(client)


class ScriptCondition:
    def __init__(self, condition: Callable[[BotClientWindow], bool]):
        self.condition: Callable[[BotClientWindow], bool] = condition

    def __call__(self, client: BotClientWindow) -> bool:
        return self.condition(client)

    @classmethod
    def client_location_name(cls, zone_name: str, *, match: bool = True):
        def _condition(client: BotClientWindow):
            logger.debug('checking location')
            if location_to_zone_map_capwords(client.location_name) == zone_name:
                logger.debug('location matches')
                return match
            logger.debug('location doesnt match')
            return not match
        return cls(_condition)

    @classmethod
    def from_yaml(cls, condition) -> Self:
        if isinstance(condition, dict):
            return cls._from_yaml(*condition.popitem())
        raise TypeError('condition must be a dict')

    @classmethod
    def _from_yaml(cls, condition_name: str, parameter) -> Self:
        return getattr(cls, condition_name)(parameter)


class ConditionalScriptStep(Generic[_T]):
    def __init__(
            self,
            steps: list[ScriptStep[_T]] | str | dict,
            pre_conditions: list[ScriptCondition] | None = None,
            conditions: list[ScriptCondition] | None = None,
            handler: ConditionalScriptStepFailedHandler | None = None,
    ):
        self.steps: list[ScriptStep[_T]] = []
        for step in steps:
            self.steps.append(ScriptAction.from_yaml(step))

        self.conditions: list[ScriptCondition] = []
        for condition in conditions or []:
            self.conditions.append(ScriptCondition.from_yaml(condition))

        self.pre_conditions: list[ScriptCondition] = []
        for pre_condition in pre_conditions or []:
            self.pre_conditions.append(ScriptCondition.from_yaml(pre_condition))

        self.handler: ConditionalScriptStepFailedHandler = handler or ConditionalScriptStepFailedHandler.restart


    def execute(self, client: BotClientWindow):
        if not any(c(client) for c in self.pre_conditions):
            return False

        for step in self.steps:
            step.execute(client)

        if all(c(client) for c in self.conditions):
            return True
        return self.handler()


class ConditionalScriptStepFailedHandler:
    def __init__(self, handler: Callable[[], bool]):
        self.handler: Callable[[], bool] = handler

    def __call__(self) -> bool:
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
    def __init__(self, *, script: dict[str, list[ScriptStep[_T] | ConditionalScriptStep[_T]]]):
        # TODO: this can handle multiple scripts per file, maybe we should support this.
        self.steps = []
        for script_name, steps in script.items():
            self.script_name = script_name
            for step in steps:
                self.steps.append(ScriptAction.from_yaml(step))

    @classmethod
    def from_yaml(cls, yaml_str: str) -> Self:
        return cls(script=yaml.safe_load(yaml_str))

    @classmethod
    def from_file(cls, yaml_file: str) -> Self:
        with open(yaml_file) as f:
            return cls.from_yaml(f)

    # def to_yaml(self) -> dict:
    #     return {self.script_name: [s.to_yaml() for s in self.steps]}

class Script(Runner):

    def __init__(self, client, script: ScriptDefinition | str):
        super().__init__(client)
        if isinstance(script, ScriptDefinition):
            self.script: ScriptDefinition = script
        elif isinstance(script, str):
            self.script: ScriptDefinition = ScriptDefinition.from_yaml(script)
        else:
            raise TypeError("script must be of type ScriptDefinition or str")

    def _run(self) -> bool:
        self._client.reset_camera()
        return all([step.execute(self._client) for step in self.script.steps])
