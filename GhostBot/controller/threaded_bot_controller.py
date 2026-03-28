import threading

from GhostBot import logger
from GhostBot.controller.bot_controller import BotController, BotClientWindow
from GhostBot.enums.bot_status import BotStatus


class ThreadedBotController(BotController):
    def __init__(self):
        super().__init__()
        self._tasks: dict[str, threading.Thread] = dict()

    def start_bot(self, client: BotClientWindow | str) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                logger.warning(f'no client {client}')
                return
        self.reload_bot_config(client)
        client.start_bot()
        self._tasks[client.name] = threading.Thread(target=self._run_bot, args=(client,))
        self._tasks.get(client.name).start()

    def _run_bot(self, client: BotClientWindow) -> None:
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
            self._tasks.get(client.name).join(timeout)
            client.bot_status = BotStatus.stopped

    def stop_bot(self, client: str | BotClientWindow, timeout=5) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                logger.warning(f'no client {client}')
                return
        if client.running:
            client.stop_bot()
            self._tasks.get(client.name).join(timeout=timeout)
            client.bot_status = BotStatus.stopped

if __name__ == '__main__':
    bot_controller = ThreadedBotController()
    try:
        bot_controller.listen()
    except KeyboardInterrupt:
        logger.info('received signal, exiting')
    finally:
        bot_controller.stop_all_bots()
