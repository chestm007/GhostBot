import os
import threading
import time
from typing import NamedTuple

import yaml
from enum import Enum

import pymem
from attrdict import AttrDict

from GhostBot import logger
from GhostBot.client_window import ClientWindow
from GhostBot.lib import vk_codes, talisman_ui_locations
from GhostBot.lib.math import linear_distance
from GhostBot.lib.talisman_ui_locations import TeamLocations

Functions = {'attack': 'attack', 'fairy': 'fairy', 'regen': 'regen', 'petfood': 'petfood'}


class Config:
    _config_dict = dict(
    mana_threshold=0.75,
    hp_threshold=0.75,
    battle_hp_threshold=0.9,
    battle_mana_threshold=0.9,
    petfood_interval=50,
    buff_interval=10,
    attacks=[['2', 1]],
    bindings=dict(
            petfood='9',
            buffs=['7'],
            sit='x',
            hp_pot='F1',
            mana_pot='F2',
            battle_hp_pot='q',
            battle_mana_pot='w',),
    functions=('attack',
               'petfood',
               'regen'),
    )

    def __init__(self, client):
        self.client = client
        self.config_filepath = self._detect_path()
        self.load()
        self.__dict__.update(self._config_dict)

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

    def load(self):
        try:
            with open(self.config_filepath, 'r') as c:
                self._config_dict = yaml.safe_load(c.read())
        except FileNotFoundError:
            self.save()

    def save(self):
        with open(self.config_filepath, 'w') as c:
            c.write(yaml.safe_dump(self._config_dict))


class ExtendedClient(ClientWindow):
    running: bool = False
    bot_status_string: str = ''
    config = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_config()

    def load_config(self):
        self.config = Config(self)

    @property
    def hp_percent(self) -> int:
        return self.hp / self.max_hp

    @property
    def mana_percent(self) -> int:
        return self.mana / self.max_mana


class BotController:
    def __init__(self):
        self.threads: dict[str, threading.Thread] = dict()
        self.clients: dict[str, ExtendedClient] = dict()
        for proc in pymem.process.list_processes():
            if proc.szExeFile == b'client.exe':
                client = ExtendedClient(proc)
                if client.name is not None and 0 < client.level <= 89:
                    self.add_client(ExtendedClient(proc))

    @property
    def client_keys(self):
        return list(str(k) for k in self.clients.keys())

    def add_client(self, client: ExtendedClient) -> None:
        self.clients[client.name] = client

    def start_bot(self, client: ExtendedClient) -> None:
        client.running = True
        client.load_config()
        self.threads[client.name] = threading.Thread(target=self._run_bot, args=(client, ))
        self.threads.get(client.name).start()

    def _run_bot(self, client: ExtendedClient) -> None:
        def determine_start_location():
            if hasattr(client.config, 'attack_spot'):
                return tuple(client.config.attack_spot)
            else:
                return client.location
        start_location = determine_start_location()

        def goto_start_location():
            while linear_distance(start_location, client.location) > 2:
                client.bot_status_string = 'go to saved spot'
                client.move_to_pos(start_location)
                time.sleep(0.5)

        attack_queue = client.config.attacks
        cur_attack_queue = None
        last_time_used_petfood = 0
        last_time_used_buffs = 0
        team_members: dict[int, ExtendedClient] = {}
        try:
            while client.running:
                # petfood logic
                if Functions['petfood'] in client.config.functions:
                    if time.time() - last_time_used_petfood > 60*client.config.petfood_interval:
                        client.press_key(vk_codes[client.config.bindings.get('petfood')])
                        last_time_used_petfood = time.time()
                        time.sleep(2)

                # buff logic
                if len(client.config.bindings.get('buffs', [])) > 0 and time.time() - last_time_used_buffs > 60*client.config.buff_interval:
                    for buff in client.config.bindings.get('buffs'):
                        client.press_key(vk_codes[buff])
                        last_time_used_buffs = time.time()
                        time.sleep(2)

                # hp/mana regen logic
                if Functions['regen'] in client.config.functions:
                    if client.hp_percent < client.config.hp_threshold or client.mana_percent < client.config.mana_threshold:
                        client.bot_status_string = 'low hp, waiting'
                        time.sleep(2)

                        if not client.in_battle:
                            goto_start_location()
                            if not client.sitting:
                                client.bot_status_string = 'sitting'
                                client.press_key(vk_codes[client.config.bindings.get('sit')])
                                # mana/hp pots?

                                if client.config.bindings.get('hp_pot') is not None:
                                    if client.hp_percent < client.config.hp_threshold:
                                        client.press_key(vk_codes[client.config.bindings.get('hp_pot')])
                                if client.config.bindings.get('mana_pot') is not None:
                                    if client.mana_percent < client.config.mana_threshold:
                                        client.press_key(vk_codes[client.config.bindings.get('mana_pot')])

                            hp = int(client.hp)
                            while client.hp < client.max_hp or client.mana < client.max_mana:  # mana check??
                                client.bot_status_string = 'healing'
                                time.sleep(0.5)
                                if client.in_battle or client.hp < hp:
                                    client.bot_status_string = 'Ouch, attacking'
                                    break
                                hp = int(client.hp)

                # Attack logic
                if Functions['attack'] in client.config.functions:
                    if client.target_hp is None or client.target_name == client.name or client.target_hp < 0:
                        client.bot_status_string = 'new target'
                        client.new_target()

                    last_time = time.time()
                    while client.target_hp and int(client.target_hp) >= 0 and client.running:
                        if client.target_name == client.name:  # if were targeting ourself, get a new target
                            break

                        # if were too far away from our start location, move back there
                        if linear_distance(start_location, client.location) > 30:
                            client.bot_status_string = 'too far go back'
                            goto_start_location()
                            break  # get a new target near our start position

                        # battle pot logic
                        if client.config.bindings.get('battle_hp_pot') is not None:
                            if client.mana_percent < client.config.battle_mana_threshold:
                                client.press_key(vk_codes[client.config.bindings.get('battle_mana_pot')])

                        if client.config.bindings.get('battle_mana_pot') is not None:
                            if client.hp_percent < client.config.battle_hp_threshold:
                                client.press_key(vk_codes[client.config.bindings.get('battle_hp_pot')])

                        if not cur_attack_queue:
                            cur_attack_queue = list(attack_queue)
                        client.bot_status_string = 'ATTACK!'
                        key, interval = cur_attack_queue.pop()
                        client.press_key(vk_codes[key])
                        time.sleep(interval)

                        if time.time() - last_time > 10:  # if we havent moved after we tried attacking, we stuck.
                            client.new_target()
                            break

                if Functions['fairy'] in client.config.functions:
                    if len(team_members) == 0:
                        client.target_self()
                        time.sleep(0.2)
                        if client.target_name != client.name:
                            client.bot_status_string = 'self not found??'
                            break
                        for member_number in client.config.fairy.get('team'):
                            client.left_click(TeamLocations[member_number])
                            time.sleep(0.2)
                            team_members[member_number] = self.clients.get(client.target_name)
                            client.bot_status_string = [m.name for m in team_members.values()]

                    for i, member in team_members.items():
                        if member.hp_percent < client.config.fairy.get('heal_at', 100):
                            client.bot_status_string = f'{member.name} {member.hp_percent}'
                            while member.hp_percent < 1:
                                 client.left_click(TeamLocations[i])
                                 client.press_key(vk_codes[client.config.bindings.get('heal')])
                                 client.bot_status_string = member.hp_percent
                            client.bot_status_string = 'healed'

                    if client.hp_percent < client.config.fairy.get('heal_self_at'):
                        client.left_click(TeamLocations[0])
                        client.press_key(vk_codes[client.config.bindings.get('heal')])
                        client.bot_status_string = 'heal self '
                    goto_start_location()

        except Exception as e:
            logger.error(e)
            print(e)

    def stop_all_bots(self, timeout=30) -> None:
        for client in self.clients.values():
            self.stop_bot(client, timeout)

    def stop_bot(self, client: ExtendedClient, timeout=1) -> None:
        if client.running:
            logger.info(f'stopping {client.name}')
            client.running = False
            self.threads.get(client.name).join(timeout=timeout)

if __name__ == '__main__':
    pass
