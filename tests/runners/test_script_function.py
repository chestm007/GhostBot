import pytest
from GhostBot.enums.bot_status import BotStatus

from tests.mocks.mock_client import client
from GhostBot.functions.script import Script, ScriptDefinition, ScriptStep, ScriptAction, ConditionalScriptStep, \
    ScriptCondition, _T


@pytest.mark.usefixtures('client')
def test_script_definition(client):
    script = ScriptDefinition(
        steps=[
            ScriptAction.move(100, 100),
            ScriptAction.move(100, 200),
            ScriptAction.move(200, 200),
            ScriptAction.attack('Rabbit'),
            ScriptAction.wait(1.5),
            ConditionalScriptStep(
                steps=[
                    ScriptAction.left_click(100, 100),
                    ScriptAction.right_click(100, 200),
                ],
                conditions=[
                    ScriptCondition(lambda client: client.location == (300, 400))
                ]
            )
        ]
    )
    client.bot_status = BotStatus.running


    script_runner = Script(client, script)
    script_runner.run()
