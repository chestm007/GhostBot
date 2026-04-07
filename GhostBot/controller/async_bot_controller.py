import asyncio
from typing import Coroutine, Any

from GhostBot import logger
from GhostBot.controller.async_task_runner import AsyncTaskRunner
from GhostBot.controller.bot_controller import BotController, BotClientWindow
from GhostBot.enums.bot_status import BotStatus
from GhostBot.server import GhostbotIPCServer


class AsyncBotController(BotController, AsyncTaskRunner):
    def __init__(self):
        AsyncTaskRunner.__init__(self)
        BotController.__init__(self)

    async def _rescan_clients(self):
        while True:
            logger.debug("Rescanning clients")
            self._scan_for_clients()
            await asyncio.sleep(2)

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
