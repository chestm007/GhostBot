from typing import TYPE_CHECKING

from GhostBot.functions import Runner

if TYPE_CHECKING:
    from GhostBot.bot_controller import ExtendedClient

class ScriptDefinition:
    """

    ..code-block:: yaml

    bc_bot:
    - move [400, 65]
    - move [375, 81]
    - move [354, 111]
    - move [336, 138]

    """
    pass

class Script(Runner):

    def _run(self) -> bool:
        pass