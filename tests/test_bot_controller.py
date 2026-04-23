from unittest.mock import MagicMock, patch

import pymem
import pytest
from pymem.ressources.structure import ProcessEntry32

import GhostBot
from GhostBot.controller.bot_controller import BotController
from GhostBot.controller.threaded_bot_controller import ThreadedBotController
from GhostBot.functions import Sell, Petfood, Regen, Buffs, Attack, Fairy
from mocks.mock_client import MockClient, client
from GhostBot.config import *

to_process = MagicMock(spec=ProcessEntry32)
def generate_process():
    with patch('GhostBot.client_window.Pointers', spec_set=True):
        proc = to_process()
        proc.process_id
        proc.szExeFile = b'client.exe'
        proc.th32ProcessID = 1234
        proc.process_id = proc.th32ProcessID
        assert proc.process_id == 1234
        return proc

@pytest.mark.usefixtures('monkeypatch', 'client')
def test_new_client_added_to_login_queue(monkeypatch, client):

    monkeypatch.setattr(GhostBot.controller.bot_controller, 'BotClientWindow', MockClient)
    monkeypatch.setattr(pymem.process, 'list_processes', lambda: [generate_process()])
    monkeypatch.setattr(pymem.Pymem, 'open_process_from_id', lambda self, _: None)
    monkeypatch.setattr(pymem.Pymem, 'check_wow64', lambda self: None)
    bot_controller = ThreadedBotController()
    bot_controller._pymem_process.list_clients = lambda : [generate_process()]
    bot_controller._remove_closed_pending_clients = lambda : None
    bot_controller._process_login_queue = lambda self: None
    bot_controller._running = True
    bot_controller._scan_for_clients()
    print(bot_controller._pymem_process.list_clients())
    print(bot_controller.clients)
    print(bot_controller._pending_clients)
    assert bot_controller.login_queue.get(1234)


@pytest.mark.usefixtures('monkeypatch', 'client')
def test_get_functions_for_client(monkeypatch, client):

    import GhostBot.functions.petfood
    monkeypatch.setattr(GhostBot.functions.petfood.Petfood, '_setup', lambda self: None)
    attack_bindings: AttackConfig.Bindings = {'battle_hp_pot': 'F1'}
    fairy_bindings: FairyConfig.Bindings = {'heal': 6}
    pet_bindings: PetConfig.Bindings = {'spawn': 'E', 'food': 9}
    regen_bindings: RegenConfig.Bindings = {'hp_pot': 'Q', 'mana_pot': 'W', 'sit': 'X'}
    config = Config(
        fairy=FairyConfig(
            bindings=fairy_bindings,
            heal_self_threshold=0.75,
            heal_team_threshold=0.5,
            spot=(123, 456),
        ), attack=AttackConfig(
            bindings=attack_bindings,
            attacks=[
                [1, 1000],
                [2, 1400]
            ],
            stuck_interval=4,
            battle_mana_threshold=0.56,
            battle_hp_threshold=0.75,
            roam_distance=40,
            spot=(123, 456),
        ), buff=BuffConfig(
            buffs=[
                [7, 2000]
            ],
            interval=10,
        ), pet=PetConfig(
            bindings=pet_bindings,
            food_interval_mins=55,
            spawn_interval_mins=55,
        ), regen=RegenConfig(
            bindings=regen_bindings,
            hp_threshold=0.75,
            mana_threshold=0.75,
        ), sell=SellConfig(
            sell_npc_name='Mr Guy Man',
            use_mount=False,
            npc_sell_click_spot=(100, 200),
            npc_search_spot=(123, 456),
        ),
    )
    client.set_config(config)
    bc = ThreadedBotController()
    _func_types = [type(f) for f in bc._get_functions_for_client(client)]
    _func_types.remove(Sell)
    _func_types.remove(Petfood)
    _func_types.remove(Regen)
    _func_types.remove(Buffs)
    _func_types.remove(Attack)
    _func_types.remove(Fairy)
    assert not _func_types
