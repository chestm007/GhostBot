import math
import threading
import time

import pymem

from GhostBot import logger
from GhostBot.client_window import ClientWindow
from GhostBot.lib import vk_codes
from GhostBot.lib.math import linear_distance


class Actions:
    pass


class ExtendedClient(ClientWindow):
    running = False
    bot_status_string = ''


class BotController:
    def __init__(self):
        self.threads: dict[str, threading.Thread] = dict()
        self.clients: dict[str, ExtendedClient] = dict()
        for proc in pymem.process.list_processes():
            if proc.szExeFile == b'client.exe':
                self.add_client(ExtendedClient(proc))

    @property
    def client_keys(self):
        return list(str(k) for k in self.clients.keys())

    def add_client(self, client: ExtendedClient) -> None:
        self.clients[client.name] = client

    def start_bot(self, client: ExtendedClient) -> None:
        client.running = True
        self.threads[client.name] = threading.Thread(target=self._run_bot, args=(client, ))
        self.threads.get(client.name).start()

    def _run_bot(self, client: ExtendedClient) -> None:

        start_location = client.location

        def goto_start_location():
            while linear_distance(start_location, client.location) > 2:
                client.bot_status_string = 'go to saved spot'
                client.move_to_pos(start_location)
                time.sleep(0.5)

        attack_queue = ['2']
        cur_attack_queue = None
        last_time_used_petfood = 0
        last_time_used_buffs = 0
        try:
            while client.running:
                # petfood logic
                if time.time() - last_time_used_petfood > 60*60:
                    client.press_key(vk_codes['9'])
                    last_time_used_petfood = time.time()
                    time.sleep(2)

                # buff logic
                if time.time() - last_time_used_buffs > 60*10:
                    #client.press_key(vk_codes['8'])
                    client.press_key(vk_codes['7'])
                    last_time_used_buffs = time.time()
                    time.sleep(2)

                # hp/mana regen logic
                if client.hp / client.max_hp < 0.75:
                    client.bot_status_string = 'low hp, waiting'
                    time.sleep(3)

                    if not client.in_battle:
                        goto_start_location()
                        if not client.sitting:
                            client.bot_status_string = 'sitting'
                            client.sit()
                            # mana/hp pots?

                        while client.hp < client.max_hp:  # mana check??
                            client.bot_status_string = 'healing'
                            time.sleep(0.5)
                            if client.in_battle:
                                client.bot_status_string = 'Ouch, attacking'
                                continue

                if client.target_name == client.name or client.target_hp < 0:
                    client.bot_status_string = 'new target'
                    client.new_target()
                last_time = time.time()
                while int(client.target_hp) > 0 and client.running:
                    if client.target_name == client.name:  # if were targeting ourself, get a new target
                        break

                    # if were too far away from our start location, move back there
                    if linear_distance(start_location, client.location) > 30:
                        client.bot_status_string = 'too far go back'
                        goto_start_location()
                        break  # get a new target near our start position

                    # TODO: battle pot logic
                    if not cur_attack_queue:
                        cur_attack_queue = list(attack_queue)
                    client.bot_status_string = 'ATTACK!'
                    client.press_key(vk_codes[cur_attack_queue.pop()])

                    if time.time() - last_time > 10:  # if we havent moved after we tried attacking, we stuck.
                        client.new_target()
                        break
        except Exception as e:
            logger.error(e)
            print(e)

    def stop_all_bots(self, timeout=30) -> None:
        for client in self.clients.values():
            self.stop_bot(client, timeout)

    def stop_bot(self, client: ExtendedClient, timeout=30) -> None:
        if client.running:
            logger.info(f'stopping {client.name}')
            client.running = False
            self.threads.get(client.name).join(timeout=timeout)
