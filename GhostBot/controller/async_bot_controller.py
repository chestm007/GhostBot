import asyncio
import logging
import time
from typing import Coroutine, Any, Callable

from GhostBot import logger
from GhostBot.controller.async_task_runner import AsyncTaskRunner
from GhostBot.controller.bot_controller import BotController, BotClientWindow
from GhostBot.controller.login_controller import LoginController
from GhostBot.enums.bot_status import BotStatus
from GhostBot.client_launcher import ClientLauncher
from GhostBot.server import GhostbotIPCServer


class AsyncBotController(BotController, AsyncTaskRunner):
    def __init__(self):
        self._controller_start_time = time.time()
        AsyncTaskRunner.__init__(self)
        BotController.__init__(self)

    @property
    def _total_running_secs(self):
        return int(time.time() - self._controller_start_time)

    async def scan_for_clients(self):
        while True:
            logger.debug("AsyncBotController :: Rescanning clients (uptime %s)", self._total_running_secs)
            await super()._scan_for_clients()
            await self._process_login_queue()
            await asyncio.sleep(2)

    async def _process_login_queue(self):

        async def callback(__client, result):
            if not result:
                logger.debug('AsyncBotController :: [%s] Login failed, removing %s from self._pending_clients', __client.process_id, __client.name)
                self._pending_clients.pop(__client.name)
            else:
                logger.debug('AsyncBotController :: :: [%s] Login succeeded', __client.process_id)

        if not self._eligible_logins():
            return

        elif len(self.login_queue) < 1:
            try:
                await LoginController._login_lock.acquire()
                await ClientLauncher().block_until_ready()
            except IndexError:
                logger.debug('AsyncBotController :: game launcher process didnt launch, retrying')
            except KeyError:
                logger.debug('AsyncBotController :: too many game launcher processes detected, there can only be one')

        for pid, _client in dict(self.login_queue).items():

            if f"task{pid}" not in self._tasks.keys():
                lc = LoginController(_client)

                if lc.current_stage == LoginController.LoginStage.character_select:
                    await asyncio.sleep(5)  # fixes a race condition with the client window opening

                char = _client.get_window_name()

                logger.debug('AsyncBotController :: self._eligible_logins :: %s', self._eligible_logins())

                if char in self._eligible_logins().keys() and _client.name is None:
                    logger.debug('AsyncBotController :: [%s|%s] resuming login procedure', pid, char)
                    _conf = self._eligible_logins().pop(char)
                elif lc.current_stage == LoginController.LoginStage.enter_credentials:
                    logger.debug('AsyncBotController :: [%s|%s] starting login procedure', pid, char)
                    _conf = self._eligible_logins().popitem()
                    char = _conf[0]
                else:
                    continue

                self._pending_clients[char] = _client

                logger.debug('AsyncBotController :: LoginStage of new pending client :: %s', lc.current_stage)

                if lc.current_stage == LoginController.LoginStage.enter_credentials:
                    logger.debug('AsyncBotController :: [%s|%s] setting config for LoginController', pid, char)
                    lc.set_config(_conf)
                super()._add_task(lc.handle_login(lambda result: callback(_client, result)), f"task{pid}")
                self.login_queue.pop(pid)

    def _add_task(self, coroutine: Callable[[BotClientWindow], Coroutine[Any, Any, Any]], client: BotClientWindow) -> str | None:
            self.reload_bot_config(client)
            client.start_bot()
            return super()._add_task(coroutine(client), client.name)

    async def _stop_task(self, client: BotClientWindow | str) -> bool:
        if isinstance(client, BotClientWindow):
            client.stop_bot()
            client.bot_status = BotStatus.stopped
            return await super()._stop_task(client.name)
        else:
            return await super()._stop_task(client)

    async def _remove_task(self, client: BotClientWindow) -> bool:
        return await super()._remove_task(client.name)

    async def _remove_all_tasks(self) -> None:
        logger.info("AsyncBotController :: Removing all tasks...")
        if "scan_for_clients" in self._tasks.keys():
            await super()._remove_task("scan_for_clients")
        for client_name in list(self._tasks.keys()):
            try:
                await self._remove_task(self.clients.get(client_name))
            except AttributeError as e:
                logger.error('AsyncBotController :: error removing task for client %s.', client_name)
                logger.exception(e)
        logger.info("AsyncBotController :: All tasks removed.")

    async def _run_bot(self, client: BotClientWindow) -> None:
        logger.info("AsyncBotController :: %s :: _run_bot()", client.name)
        client.bot_status = BotStatus.started

        functions = list(self._get_functions_for_client(client))
        logger.info("AsyncBotController :: %s :: _run_bot: %s", client.name, functions)

        while client.running:
            client.bot_status = BotStatus.running
            if client.disconnected:
                client.bot_status = BotStatus.disconnected
                logger.info("AsyncBotController :: %s :: disconnected.", client.name)
                break
            for function in functions:
                try:
                    await function.run()
                    await asyncio.sleep(0.1)  # FIXME: this pause ensures all client runners get a chance to execute

                except Exception as e:
                    logger.error('AsyncBotController :: Error running %s :: %s, Traceback to follow', function.__class__.__name__, client.name)
                    logger.exception(e)

        client.bot_status = BotStatus.stopped
        logger.info("AsyncBotController :: %s :: Stopped.", client.name)

    def start_bot(self, client: BotClientWindow | str) -> None:
        if isinstance(client, str):
            client = self.get_client(client)
        self._add_task(self._run_bot, client=client)

    async def stop_all_bots(self, timeout=30) -> None:
        await self._remove_all_tasks()

    async def stop_bot(self, client: str | BotClientWindow, timeout=5) -> None:
        if isinstance(client, str):
            client = self.get_client(client)
        await self._remove_task(client)

    async def listen(self, host=None, port=None):
        self._controller_start_time = time.time()
        try:
            super()._add_task(self.scan_for_clients(), "scan_for_clients")
            server = GhostbotIPCServer(bot_controller=self, host=host, port=port)
            await server.run_server()
        except KeyboardInterrupt:
            await self.stop_all_bots()
            await self._stop_all_tasks()

def main():
    import os

    if os.environ.get('PYCHARM_HOSTED'):
        logger.setLevel(logging.DEBUG)

    asyncio.run(AsyncBotController().listen())

if __name__ == '__main__':
    main()