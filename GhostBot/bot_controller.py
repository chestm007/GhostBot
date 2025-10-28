import os
import threading
from typing import List, Optional, TypedDict, Tuple

import yaml
import pymem

from GhostBot import logger
from GhostBot.client_window import ClientWindow
from GhostBot.functions import Attack, Buffs, Fairy, Petfood, Regen
from GhostBot.lib.win32.process import PymemProcess

Functions = {'attack': 'attack', 'fairy': 'fairy', 'regen': 'regen', 'petfood': 'petfood'}


class Config:

    mana_threshold: int
    hp_threshold: int
    hattle_hp_threshold: int
    petfood_interval: int
    buff_interval: int
    unstuck: bool
    stuck_interval: int
    attacks: List[List[int]]  # Change to tuple
    bindings: TypedDict('BindingsDict', {
        'petfood': str,
        'buffs': List[str],
        'sit': str,
        'hp_pot': str,
        'mana_pot': str,
        'battle_hp_pot': str,
        'battle_mana_pot': str,
        'pet': 'str'
    })
    functions: Tuple[str, ...]

    # This should be the absolute bare minimum defaults required to get the bot running
    _config_dict = dict(
        mana_threshold=0.75,
        hp_threshold=0.75,
        battle_hp_threshold=0.9,
        battle_mana_threshold=0.9,
        petfood_interval=50,
        buff_interval=10,
        unstuck=True,
        stuck_interval=10,
        attacks=[['2', 1]],
        bindings=dict(
                petfood='9',
                buffs=['7'],
                sit='x',
                hp_pot='F1',
                mana_pot='F2',
                battle_hp_pot='Q',
                battle_mana_pot='W',
                pet='E'
        ),
        functions=('attack',
                   'petfood',
                   'regen',
                   'buffs',
        ),
    )

    def __init__(self, client):
        self.client = client
        self.config_filepath = self._detect_path()
        #self.load()
        self.update()

    def update(self):
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
                self._config_dict.update(yaml.safe_load(c.read()))  # overwrite config defaults with whats in the loaded config
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

    def load_config(self, config: Config=None):
        # TODO: we should do some validation of the config schema....
        logger.debug('loading config')
        if config is None:
            logger.debug('config created')
            self.config = Config(self)
        else:
            logger.debug('config loaded')
            self.config = config

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

        # TODO: maybe we want to scan this again to refresh the client list?
        for proc in PymemProcess.list_clients():
            client = ExtendedClient(proc)
            try:
                if client.name is not None and 0 < client.level <= 89:  # and client.name not in self.clients.keys()
                    logger.info(f'adding client {client.name}')
                    self.add_client(ExtendedClient(proc))
            except TypeError:
                # TODO: do i want to track this for the autologin? might be an alright hook
                #       especially if we know which char to log...
                logger.info(f'cannot add client {proc}')

    @property
    def client_keys(self) -> List[str]:
        return list(str(k) for k in self.clients.keys())

    def add_client(self, client: ExtendedClient) -> None:
        self.clients[client.name] = client

    def start_bot(self, client: ExtendedClient) -> None:
        client.bot_status_string = 'Starting.'
        client.running = True
        client.load_config()
        self.threads[client.name] = threading.Thread(target=self._run_bot, args=(client, ))
        self.threads.get(client.name).start()

    def get_client(self, name) -> Optional[List[ExtendedClient]]:
        return self.clients.get(name)

    def _run_bot(self, client: ExtendedClient) -> None:
        client.bot_status_string = 'Started.'

        _runners = {
            'petfood': Petfood(client),
            'regen': Regen(client),
            'buffs': Buffs(client),
            'attack': Attack(client),
            'fairy': Fairy(self, client)
        }

        while client.running:
            client.bot_status_string = 'Running'
            try:
                for function in client.config.functions:
                    logger.debug(f'{client.name}: Running function {function }')
                    _runners.get(function).run()

            except Exception as e:
                logger.exception(e)
        client.bot_status_string = 'Stopped'

    def stop_all_bots(self, timeout=30) -> None:
        for client in self.clients.values():
            self.stop_bot(client, timeout)

    def stop_bot(self, client: ExtendedClient, timeout=1) -> None:
        if client.running:
            logger.info(f'{client.name}: Stopping')
            client.running = False
            self.threads.get(client.name).join(timeout=timeout)

if __name__ == '__main__':
    pass
