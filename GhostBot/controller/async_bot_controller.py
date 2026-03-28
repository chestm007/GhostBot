import asyncio
from typing import Coroutine, Any

from GhostBot import logger
from GhostBot.controller.bot_controller import BotController, BotClientWindow
from GhostBot.enums.bot_status import BotStatus
from GhostBot.server import GhostbotIPCServer


class AsyncBotController(BotController):
    def __init__(self):
        super().__init__()
        self._tasks: dict[str, asyncio.Task] = dict()

    async def _add_task(self, coroutine: Coroutine[Any, Any, Any], client_name: str) -> str | None:
            """
            Adds a new asynchronous task to the runner.

            :param coroutine: The coroutine function to be run as a task.
            :param client_name: An optional name for the task for easier identification.
            :returns: The unique ID of the newly added task.
            """
            if not asyncio.iscoroutine(coroutine):
                raise TypeError("Only coroutines can be added as tasks.")

            # Create the asyncio.Task. It won't start running until the event loop gets to it.
            task = asyncio.create_task(coroutine, name=client_name)
            self._tasks[client_name] = task
            print(f"Task '{client_name}' added.")
            return client_name

    async def _stop_task(self, client_name: str) -> bool:
        """
        Stops a running task.

        :param client_name: The ID of the task to stop.
        :returns: True if the task was found and successfully cancelled, False otherwise.
        """
        if client_name in self._tasks:
            task = self._tasks[client_name]
            if not task.done():
                task.cancel()
                try:
                    # Awaiting the cancelled task to handle potential exceptions
                    await task
                except asyncio.CancelledError:
                    print(f"Task '{client_name}' successfully cancelled.")
                    # We can optionally remove it after cancellation if we don't want to track finished tasks
                    # del self._tasks[client_name]
                    return True
            else:
                print(f"Task '{client_name}' is already done and cannot be cancelled.")
                return False
        else:
            print(f"Task '{client_name}' not found.")
            return False

    async def _remove_task(self, client_name: str) -> bool:
        """
        Removes a task from the runner. If the task is running, it will be cancelled first.

        :param client_name: The ID of the task to remove.
        :returns: True if the task was found and removed, False otherwise.
        """
        if client_name in self._tasks:
            task = self._tasks[client_name]
            if not task.done():
                await self._stop_task(client_name) # Ensure it's cancelled before removing
            del self._tasks[client_name]
            print(f"Task '{client_name}' removed.")
            return True
        else:
            print(f"Task '{client_name}' not found.")
            return False

    def _get_task_status(self, task_id: str) -> str:
        """Gets the status of a specific task."""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            if task.cancelled():
                return "cancelled"
            elif task.done():
                return "done"
            elif task._state == 'PENDING':  # Check if the task is pending
                return "pending"
            else:
                return "running"  # If it's not done or cancelled, it must be running
        else:
            return "not_found"

    def _list_tasks(self) -> dict[str, str]:
        """
        Lists all tasks currently managed by the runner and their statuses.

        Returns:
            A dictionary where keys are task IDs and values are their statuses.
        """
        status_dict = {}
        for task_id, task in self._tasks.items():
            status_dict[task_id] = self._get_task_status(task_id)
        return status_dict

    async def _stop_all_tasks(self) -> None:
        """
        Stops all currently running tasks.
        """
        print("Stopping all tasks...")
        tasks_to_cancel = list(self._tasks.values())
        for task in tasks_to_cancel:
            if not task.done():
                task.cancel()
        # Wait for all cancellations to be processed
        await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
        print("All tasks stopped.")

    async def _remove_all_tasks(self) -> None:
        """
        Removes all tasks from the runner. This will also stop them if they are running.
        """
        print("Removing all tasks...")
        for client_name in list(self._tasks.keys()):
            await self._remove_task(client_name)
        print("All tasks removed.")

    async def _run_bot(self, client: BotClientWindow) -> None:
        client.bot_status = BotStatus.started

        functions = list(self._get_functions_for_client(client))

        while client.running:
            client.bot_status = BotStatus.running
            if client.disconnected:
                logger.info(f"{client.name}: disconnected.")
                break
            try:
                for function in functions:
                    await function.run()

            except Exception as e:
                logger.exception(e)
        client.bot_status = BotStatus.stopped
        logger.info(f"{client.name}: Stopped.")

    async def start_bot(self, client: BotClientWindow | str) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                logger.warning(f'no client {client}')
                return
        await self._add_task(self._run_bot(client), client_name=client.name)

    async def stop_all_bots(self, timeout=30) -> None:
        await self._remove_all_tasks()

    async def stop_bot(self, client: str | BotClientWindow, timeout=5) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                logger.warning(f'no client {client}')
                return
        await self._remove_task(client.name)

    async def listen(self, host=None, port=None):
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
