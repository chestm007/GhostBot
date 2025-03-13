import threading
import time

import pymem

from GhostBot import logger
from GhostBot.client_window import ClientWindow
from GhostBot.lib import vk_codes


class Actions:
    pass

class BotController:
    def __init__(self):
        self.threads: dict[str, threading.Thread] = dict()
        self.clients: dict[str, ClientWindow] = dict()
        for proc in pymem.process.list_processes():
            if proc.szExeFile == b'client.exe':
                self.add_client(ClientWindow(proc))

    @property
    def client_keys(self):
        return list(str(k) for k in self.clients.keys())

    def add_client(self, client: ClientWindow) -> None:
        self.clients[client.name] = client

    def start_bot(self, client: ClientWindow) -> None:
        client.running = True
        self.threads[client.name] = threading.Thread(target=self._run_bot, args=(client, ))
        self.threads.get(client.name).start()

    def _run_bot(self, client: ClientWindow) -> None:
        client.left_click(100, 200)
        return
        attack_queue = ['3']
        cur_attack_queue = None
        try:
            while client.running:
                # TODO: petfood logic
                # TODO: buff logic
                # TODO: hp/mana regen logic
                client.new_target()
                last_time = time.time()
                while int(client.target_hp) > 0 and client.running:
                    # TODO: battle pot logic
                    if not cur_attack_queue:
                        cur_attack_queue = list(attack_queue)
                    client.press_key(vk_codes[cur_attack_queue.pop()])

                    if time.time() - last_time > 10:  # if we havent moved after we tried attacking, we stuck.
                        break
        except Exception as e:
            logger.error(e)
            print(e)

    def stop_all_bots(self, timeout=30) -> None:
        for client in self.clients.values():
            self.stop_bot(client, timeout)

    def stop_bot(self, client, timeout=30) -> None:
        if client.running:
            logger.info(f'stopping {client.name}')
            client.running = False
            self.threads.get(client.name).join(timeout=timeout)
