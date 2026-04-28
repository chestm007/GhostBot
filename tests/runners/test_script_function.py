import logging

import pytest
from GhostBot.controller.threaded_bot_controller import ThreadedBotController

from GhostBot.enums.bot_status import BotStatus

from tests.mocks.mock_client import client
from GhostBot.functions.script import Script, ScriptDefinition, ScriptAction, ConditionalScriptStep, \
    ScriptCondition

from GhostBot import logger
logger.setLevel(logging.DEBUG)


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

@pytest.mark.skip("local testing only")
def test_jc_rep_script():
    script_str = """
    jc_rep_daily:
    - conditional_loop:
        pre_conditions:
        - client_location_name: Stone City
        # - client_location_name: Sky Village  # uncomment to test failure
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

    bc = ThreadedBotController()
    bc._running = True
    bc._scan_for_clients()
    wyp = bc.clients.get('bot_name')
    wyp.bot_status = BotStatus.running
    wyp.running = True
    script_runner = Script(wyp, script_str)
    assert script_runner.run()


def test_jc_manager_congcan_daily():
    logger.debug = print
    script_str = """
    jc_manager_cogren_daily:
    - conditional_loop:
        pre_conditions:
        - client_location_name: Jade City
        # - client_location_name: Sky Village  # uncomment to test failure
        handler: ignore
        steps:
        # Goto Manager - Ren Congcan
        - goto_npc:
            npc_name: Ren Congcan
        - wait: 2
        
        # Accept Quests
        - click_npc
        - wait: 2
        - left_click: 344 450
        - wait: 2
        - left_click: 318 654  # click accept
        - wait: 2
        - left_click: 359 657  # click close
        - wait: 2
        - click_npc
        - wait: 2
        - left_click: 335 418
        - wait: 2
        - left_click: 318 654  # click accept
        - wait: 2
        - left_click: 359 657  # click close
        - wait: 2
        
        # Black Marketer
        - goto_npc:
            npc_name: Black Marketer
        - wait: 2
        - select_npc
        - wait: 2
        - left_click: 1001 604
        - wait: 2
        
        # Ma Lo
        - goto_npc:
            npc_name: Minister Ma Lo
        - wait: 2
        - select_npc
        - wait: 2
        - left_click: 957 601
        - wait: 2
        
        # hand in quests
        - goto_npc:
            npc_name: Ren Congcan
        - wait: 2
        - click_npc
        - wait: 0.5
        - click_npc
        - wait: 2
        - left_click: 344 450
        - wait: 2
        - left_click: 318 654  # click accomplish
        - wait: 2
        - click_npc
        - wait: 0.5
        - click_npc
        - wait: 2
        - left_click: 346 417
        - wait: 2
        - left_click: 318 654  # click accomplish
        - wait: 2
    """

    bc = ThreadedBotController()
    bc._running = True
    bc._scan_for_clients()
    wyp = bc.clients.get('bot_name')
    wyp.bot_status = BotStatus.running
    wyp.running = True
    script_runner = Script(wyp, script_str)
    assert script_runner.run()
