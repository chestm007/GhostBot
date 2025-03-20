import os
import threading
import yaml
import pymem

from GhostBot import logger
from GhostBot.client_window import ClientWindow
from GhostBot.functions import Attack, Buffs, Fairy, Petfood, Regen, Locational

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
                   'regen',
                   'buffs'),
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
        # TODO: we should do some validation of the config schema....
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
        client.bot_status_string = 'Starting'
        def determine_start_location():
            if hasattr(client.config, 'attack_spot'):
                return tuple(client.config.attack_spot)
            else:
                return client.location

        _runners = {
            'petfood': Petfood,
            'regen': Regen,
            'buffs': Buffs,
            'attack': Attack,
            'fairy': Fairy
        }

        loc = determine_start_location()
        logger.info(f'{client.name}: setting start location {loc}')
        for key, runner in _runners.items():
            _runners[key] = runner(client)
            if issubclass(runner, Locational):  # TODO: this is a filthy hack.
                runner.start_location = loc

        while client.running:
            client.bot_status_string = 'Running'
            try:
                for function in client.config.functions:
                    logger.debug(f'{client.name}: Running function {function }')
                    _runners.get(function).run()

            except Exception as e:
                logger.error(e)
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
