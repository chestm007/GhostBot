import asyncio
from typing import Coroutine, Any

from GhostBot import logger


class AsyncTaskRunner:
    def __init__(self):
        self._tasks: dict[str, asyncio.Task] = dict()

    def _add_task(self, coroutine: Coroutine[Any, Any, Any], task_name: str) -> str | None:
        """
        Adds a new asynchronous task to the runner.

        :returns: The unique ID of the newly added task.
        """
        if not asyncio.iscoroutine(coroutine):
            raise TypeError("Only coroutines can be added as tasks.")

        # Create the asyncio.Task. It won't start running until the event loop gets to it.
        task = asyncio.create_task(coroutine, name=task_name)
        self._tasks[task_name] = task
        logger.info("AsyncTaskRunner :: Task '%s' added.", task_name)
        return task_name

    async def _stop_task(self, task_name: str) -> bool:
        """
        Stops a running task.

        :returns: True if the task was found and successfully cancelled, False otherwise.
        """
        if task_name in self._tasks:
            task = self._tasks[task_name]
            if not task.done():
                task.cancel()
                try:
                    # Awaiting the cancelled task to handle potential exceptions
                    await task
                except asyncio.CancelledError:
                    logger.info("AsyncTaskRunner :: Task '%s' successfully cancelled.", task_name)
                    # We can optionally remove it after cancellation if we don't want to track finished tasks
                    # del self._tasks[task_name]
                    return True
            else:
                logger.info("AsyncTaskRunner :: Task '%s' is already done and cannot be cancelled.", task_name)
        else:
            logger.info("AsyncTaskRunner :: Task '%s' not found.", task_name)
        return False

    async def _remove_task(self, task_name: str) -> bool:
        """
        Removes a task from the runner. If the task is running, it will be cancelled first.

        :returns: True if the task was found and removed, False otherwise.
        """
        if task_name in self._tasks:
            task = self._tasks[task_name]
            if not task.done():
                await self._stop_task(task_name)  # Ensure it's cancelled before removing
            del self._tasks[task_name]
            logger.info("AsyncTaskRunner :: Task '%s' removed.", task_name)
            return True
        else:
            logger.info("AsyncTaskRunner :: Task '%s' not found.", task_name)
            return False

    def _get_task_status(self, task_name: str) -> str:
        """Gets the status of a specific task."""
        if task_name in self._tasks:
            task = self._tasks[task_name]
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
        for task_name, task in self._tasks.items():
            status_dict[task_name] = self._get_task_status(task_name)
        return status_dict

    async def _stop_all_tasks(self) -> None:
        """
        Stops all currently running tasks.
        """
        logger.info("AsyncTaskRunner :: Stopping all tasks...")
        for task_name, task in self._tasks.items():
            if not task.done():
                logger.info("AsyncTaskRunner :: cancelling task '%s'.", task_name)
                task.cancel()
            else:
                logger.info("AsyncTaskRunner :: task already done '%s'.", task_name)
        # Wait for all cancellations to be processed
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        logger.info("AsyncTaskRunner :: All tasks stopped.")

    async def _remove_all_tasks(self) -> None:
        """
        Removes all tasks from the runner. This will also stop them if they are running.
        """
        logger.info("AsyncTaskRunner :: Removing all tasks...")
        for task_name in list(self._tasks.keys()):
            await self._remove_task(task_name)
        logger.info("AsyncTaskRunner :: All tasks removed.")
