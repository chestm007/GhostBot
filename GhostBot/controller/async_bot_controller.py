import asyncio
import logging
from typing import Coroutine, Any

from GhostBot import logger
from GhostBot.controller.async_task_runner import AsyncTaskRunner
from GhostBot.controller.bot_controller import BotController, BotClientWindow
from GhostBot.controller.login_controller import LoginController
from GhostBot.enums.bot_status import BotStatus
from GhostBot.client_launcher import ClientLauncher
from GhostBot.server import GhostbotIPCServer


class AsyncBotController(BotController, AsyncTaskRunner):
    def __init__(self):
        AsyncTaskRunner.__init__(self)
        BotController.__init__(self)

    async def _rescan_clients(self):
        while True:
            logger.debug("Rescanning clients")
            self._scan_for_clients()
            await self._process_login_queue()
            await asyncio.sleep(2)

    async def _process_login_queue(self):

        async def callback(__client, result):
            if not result:
                logger.debug(f'{self.__class__.__name__} :: [{__client.process_id}] Login failed, removing {__client.name} from self._pending_clients')
                self._pending_clients.pop(__client.name)
            else:
                logger.debug(f'{self.__class__.__name__} :: [{__client.process_id}] Login succeeded')

        logger.debug('%s :: self._eligible_logins :: %s', self.__class__.__name__, self._eligible_logins())

        if not self._eligible_logins():
            return
        elif len(self.login_queue) < 1:
            await ClientLauncher().block_until_ready()

        for pid, _client in dict(self.login_queue).items():

            if f"task{pid}" not in self._tasks.keys():
                lc = LoginController(_client)

                if lc.current_stage == LoginController.LoginStage.character_select:
                    await asyncio.sleep(5)  # fixes a race condition with the client window opening

                char = _client.get_window_name()

                if char in self._eligible_logins().keys() and _client.name is None:
                    logger.debug('[%s] resuming login procedure', pid)
                    _conf = self._eligible_logins().pop(char)
                elif lc.current_stage == LoginController.LoginStage.enter_credentials:
                    logger.debug('[%s] starting login procedure', pid)
                    _conf = self._eligible_logins().popitem()
                    char = _conf[0]
                else:
                    continue

                self._pending_clients[char] = _client

                if lc.current_stage == LoginController.LoginStage.enter_credentials:
                    logger.debug('[%s] setting config for LoginController', pid)
                    lc.set_config(_conf)
                super()._add_task(lc.handle_login(lambda result: callback(_client, result)), f"task{pid}")
                self.login_queue.pop(pid)

    def _add_task(self, coroutine: Coroutine[Any, Any, Any], client: BotClientWindow) -> str | None:
            self.reload_bot_config(client)
            client.start_bot()
            return super()._add_task(coroutine, client.name)

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
        print("Removing all tasks...")
        if "rescan clients" in self._tasks.keys():
            await super()._remove_task("rescan clients")
        for client_name in list(self._tasks.keys()):
            await self._remove_task(self.clients.get(client_name))
        print("All tasks removed.")

    async def _run_bot(self, client: BotClientWindow) -> None:
        logger.info(f"{client.name}: _run_bot()")
        client.bot_status = BotStatus.started

        functions = list(self._get_functions_for_client(client))
        logger.info(f"{client.name}: _run_bot: {functions}")

        while client.running:
            client.bot_status = BotStatus.running
            if client.disconnected:
                client.bot_status = BotStatus.disconnected
                logger.info(f"{client.name}: disconnected.")
                break
            for function in functions:
                try:
                    await function.run()
                    await asyncio.sleep(0.1)  # FIXME: this pause ensures all client runners get a chance to execute

                except Exception as e:
                    logger.exception(f"Exception running {function.__class__.__name__} :: {client.name} :: {e}")

        client.bot_status = BotStatus.stopped
        logger.info(f"{client.name}: Stopped.")

    def start_bot(self, client: BotClientWindow | str) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                logger.warning(f'no client {client}')
                return
        self._add_task(self._run_bot(client), client=client)

    async def stop_all_bots(self, timeout=30) -> None:
        await self._remove_all_tasks()

    async def stop_bot(self, client: str | BotClientWindow, timeout=5) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                logger.warning(f'no client {client}')
                return
        await self._remove_task(client)

    async def listen(self, host=None, port=None):
        super()._add_task(self._rescan_clients(), "rescan clients")
        server = GhostbotIPCServer(bot_controller=self, host=host, port=port)
        await server.run_server()

if __name__ == '__main__':
    async def run():
        try:
            await bot_controller.listen()
        except KeyboardInterrupt:
            logger.info('received signal, exiting')
        finally:
            await bot_controller.stop_all_bots()
    bot_controller = AsyncBotController()
    asyncio.run(run())
