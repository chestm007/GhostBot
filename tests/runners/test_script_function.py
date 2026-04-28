import pytest
from GhostBot.controller.threaded_bot_controller import ThreadedBotController

from GhostBot.enums.bot_status import BotStatus

from tests.mocks.mock_client import client
from GhostBot.functions.script import Script, ScriptDefinition, ScriptStep, ScriptAction, ConditionalScriptStep, \
    ScriptCondition, _T


@pytest.mark.usefixtures('client')
def test_script_definition(client):
    script = ScriptDefinition(
        script={'test': [
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
        ]}
    )
    client.bot_status = BotStatus.running


    script_runner = Script(client, script)
    script_runner.run()


def test_jc_rep_script():
    script_str = """
    jc_rep_daily:
    - conditional_loop:
        pre_conditions:
        - client_location_name: Stone City
        handler: ignore
        steps:
        # Goto Immortal Lee
        - move: 278 -522
        - wait: 2
        - click_npc
        - wait: 2
        # Buy Shit
        - left_click: 296 432
        - wait: 2
        - loop:
            count: 6
            steps:
              - left_click: 199 295
        - left_click: 185 716
        - goto_npc:
            npc_name: Arcane Warrior
        - wait: 2
        - click_npc
        - wait: 2
        # Accept Quest
        - left_click: 305 625
        - wait: 2
        - left_click: 305 660
        - wait: 2
        - left_click: 367 659
        - wait: 2
        # Complete Quest
        - click_npc
        - wait: 2
        - left_click: 338 607
        - wait: 1
        - left_click: 306 660
        - wait: 1
        - move: 290 -480
    """

    import pprint

    bc = ThreadedBotController()
    bc._running = True
    bc._scan_for_clients()
    wyp = bc.clients.get('bot_name')
    wyp.bot_status = BotStatus.running
    wyp.running = True
    script_runner = Script(wyp, script_str)
    pprint.pprint(script_runner.script.steps[0].steps)
    assert script_runner.run()
