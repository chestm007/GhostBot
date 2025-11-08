import threading
from typing import Generator

from GhostBot import logger
from GhostBot.client_window import ClientWindow
from GhostBot.config import Config, ConfigLoader
from GhostBot.enums.bot_status import BotStatus
from GhostBot.functions import Attack, Buffs, Fairy, Petfood, Regen, Runner, Sell, Delete
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.server import GhostbotIPCServer


class ExtendedClient(ClientWindow):
    running: bool = False
    bot_status: BotStatus = BotStatus.created
    config: Config = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_config()

    def to_json(self) -> dict:
        return dict(
            name=self.name,
            status=self.bot_status.name,
            hp=self.hp,
            mana=self.mana,
            max_hp=self.max_hp,
            max_mana=self.max_mana,
            level=self.level,
            target_name=self.target_name,
            target_hp=self.target_hp,
            location_x=self.location_x,
            location_y=self.location_y,
            location_name=self.location_name,
            pet_active=self.pet_active,
            sitting=self.sitting,
            in_battle=self.in_battle,
            inventory_open=self.inventory_open,
            #target_location=self.target_location,
            mounted=self.on_mount,
            window_pos=self.get_window_pos(),
            window_size=self.get_window_size(),
        )

    def mount(self, _key=0):
        if (self.config.sell is not None
            and self.config.sell.use_mount
        ):
            super().mount(_key)

    def unmount(self, _key=0):
        if (self.config.sell is not None
            and self.config.sell.use_mount
        ):
            super().dismount(_key)

    def load_config(self):
        self.set_config(ConfigLoader(self).load())

    def set_config(self, config: Config):
        self.config = config

    @property
    def bot_status_string(self) -> str:
        return str(self.bot_status.name)

    @property
    def hp_percent(self) -> float:
        return self.hp / self.max_hp

    @property
    def mana_percent(self) -> float:
        return self.mana / self.max_mana

    def start_bot(self):
        logger.info(f'{self.name}: Starting...')
        self.bot_status = BotStatus.starting
        self.running = True
        self.load_config()

    def stop_bot(self):
        logger.info(f'{self.name}: Stopping...')
        self.bot_status = BotStatus.stopping
        self.running = False

class BotController:

    def __init__(self):
        self.threads: dict[str, threading.Thread] = dict()
        self.clients: dict[str, ExtendedClient] = dict()

        # TODO: maybe we want to scan this again to refresh the client list?
        for proc in PymemProcess.list_clients():
            client = ExtendedClient(proc)
            try:
                if client.name is not None and 0 < client.level <= 89:  # and client.name not in self.clients.keys()
                    if client.name not in self.clients.keys():
                        logger.info(f'adding client {client.name}')
                        self.add_client(ExtendedClient(proc))
                    else:
                        logger.info(f'client {client.name} already exists, skipping')
            except (TypeError, AttributeError):
                # TODO: do i want to track this for the autologin? might be an alright hook
                #       especially if we know which char to log...
                logger.info(f'cannot add client {proc}')

    @property
    def client_keys(self) -> list[str]:
        return list(str(k) for k in self.clients.keys())

    def add_client(self, client: ExtendedClient) -> None:
        self.clients[client.name] = client

    def start_bot(self, client: ExtendedClient | str) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                logger.warning(f'no client {client}')
                return
        self.reload_bot_config(client)
        client.start_bot()
        self.threads[client.name] = threading.Thread(target=self._run_bot, args=(client, ))
        self.threads.get(client.name).start()

    def reload_bot_config(self, client: str | ExtendedClient) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                logger.warning(f'no client {client}')
                return
        client.load_config()

    def get_client(self, name) -> ExtendedClient | None:
        return self.clients.get(name)

    def _run_bot(self, client: ExtendedClient) -> None:
        client.bot_status = BotStatus.started

        functions = list(self._get_functions_for_client(client))

        while client.running:
            client.bot_status = BotStatus.running
            if client.disconnected:
                logger.info(f"{client.name}: disconnected.")
                break
            try:
                for function in functions:
                    function.run()

            except Exception as e:
                logger.exception(e)
        client.bot_status = BotStatus.stopped
        logger.info(f"{client.name}: Stopped.")

    def _get_functions_for_client(self, client: ExtendedClient) -> Generator[Runner, None, None]:
        if client.config.delete is not None:
            yield Delete(client)
        if client.config.sell is not None:
            yield Sell(client)
        if client.config.pet is not None:
            yield Petfood(client)
        if client.config.regen is not None:
            yield Regen(client)
        if client.config.buff is not None:
            yield Buffs(client)
        if client.config.attack is not None:
            yield Attack(client)
        if client.config.fairy is not None:
            yield Fairy(self, client)

    def stop_all_bots(self, timeout=30) -> None:
        logger.info("stopping all bots...")
        _stopping = []
        for client in self.clients.values():
            if client.running:
                logger.info(f'stopping client {client.name}')
                client.stop_bot()
                _stopping.append(client)
        for client in _stopping:
            logger.debug(f'joining thread {client.name}')
            self.threads.get(client.name).join(timeout)
            client.bot_status = BotStatus.stopped

    def stop_bot(self, client: str | ExtendedClient, timeout=5) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                logger.warning(f'no client {client}')
                return
        if client.running:
            client.stop_bot()
            self.threads.get(client.name).join(timeout=timeout)
            client.bot_status = BotStatus.stopped

    def listen(self, host=None, port=None):
        server = GhostbotIPCServer(bot_controller=self, host=host, port=port)
        server.listen()

if __name__ == '__main__':
    bot_controller = BotController()
    try:
        bot_controller.listen()
    except KeyboardInterrupt as e:
        logger.info('received signal, exiting')
    finally:
        bot_controller.stop_all_bots()
