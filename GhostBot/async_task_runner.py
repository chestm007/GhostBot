import asyncio
from typing import Dict, Any, Coroutine, Optional

class AsyncTaskRunner:
    def __init__(self):
        # A dictionary to store our running tasks.
        # The key will be a unique task ID, and the value will be the asyncio.Task object.
        self._tasks: Dict[str, asyncio.Task] = {}
        # A counter to generate unique IDs for tasks.
        self._next_task_id = 0

    def _generate_task_id(self) -> str:
        """Generates a unique ID for each task."""
        task_id = f"task_{self._next_task_id}"
        self._next_task_id += 1
        return task_id

    async def add_task(self, coroutine: Coroutine[Any, Any, Any], task_name: Optional[str] = None) -> str:
        """
        Adds a new asynchronous task to the runner.

        Args:
            coroutine: The coroutine function to be run as a task.
            task_name: An optional name for the task for easier identification.

        Returns:
            The unique ID of the newly added task.
        """
        if not asyncio.iscoroutine(coroutine):
            raise TypeError("Only coroutines can be added as tasks.")

        task_id = self._generate_task_id()
        if task_name:
            task_id = f"{task_name}_{task_id}" # Prepend user-defined name for clarity

        # Create the asyncio.Task. It won't start running until the event loop gets to it.
        task = asyncio.create_task(coroutine, name=task_id)
        self._tasks[task_id] = task
        print(f"Task '{task_id}' added.")
        return task_id

    async def start_task(self, task_id: str) -> bool:
        """
        Starts a task that has been added but not yet running (though asyncio.create_task
        already schedules it, this method can be used for explicit control or
        if you were to implement a 'paused' state later).

        For this implementation, 'starting' a task means ensuring it's in the _tasks
        dictionary and allowing the event loop to run it.

        Args:
            task_id: The ID of the task to start.

        Returns:
            True if the task was found and is now managed by the runner, False otherwise.
        """
        if task_id in self._tasks:
            # asyncio.create_task already schedules the coroutine.
            # If the task was cancelled or finished, this won't restart it.
            # For true restart, you'd need to re-add it.
            if self._tasks[task_id].done():
                print(f"Task '{task_id}' has already completed or been cancelled. Cannot restart.")
                return False
            print(f"Task '{task_id}' is already scheduled to run or running.")
            return True
        else:
            print(f"Task '{task_id}' not found.")
            return False

    async def stop_task(self, task_id: str) -> bool:
        """
        Stops a running task.

        Args:
            task_id: The ID of the task to stop.

        Returns:
            True if the task was found and successfully cancelled, False otherwise.
        """
        if task_id in self._tasks:
            task = self._tasks[task_id]
            if not task.done():
                task.cancel()
                try:
                    # Awaiting the cancelled task to handle potential exceptions
                    await task
                except asyncio.CancelledError:
                    print(f"Task '{task_id}' successfully cancelled.")
                    # We can optionally remove it after cancellation if we don't want to track finished tasks
                    # del self._tasks[task_id]
                    return True
            else:
                print(f"Task '{task_id}' is already done and cannot be cancelled.")
                return False
        else:
            print(f"Task '{task_id}' not found.")
            return False

    async def remove_task(self, task_id: str) -> bool:
        """
        Removes a task from the runner. If the task is running, it will be cancelled first.

        Args:
            task_id: The ID of the task to remove.

        Returns:
            True if the task was found and removed, False otherwise.
        """
        if task_id in self._tasks:
            task = self._tasks[task_id]
            if not task.done():
                await self.stop_task(task_id) # Ensure it's cancelled before removing
            del self._tasks[task_id]
            print(f"Task '{task_id}' removed.")
            return True
        else:
            print(f"Task '{task_id}' not found.")
            return False

    # def get_task_status(self, task_id: str) -> str:
    #     """
    #     Gets the status of a specific task.
    #
    #     Args:
    #         task_id: The ID of the task to check.
    #
    #     Returns:
    #         A string representing the task's status (e.g., 'running', 'done', 'pending', 'not_found').
    #     """
    #     if task_id in self._tasks:
    #         task = self._tasks[task_id]
    #         if task.cancelled():
    #             return "cancelled"
    #         elif task.done():
    #             return "done"
    #         elif task.running():
    #             return "running"
    #         else:
    #             return "pending" # Task is created but not yet running by the event loop
    #     else:
    #         return "not_found"

    def get_task_status(self, task_id: str) -> str:
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

    def list_tasks(self) -> Dict[str, str]:
        """
        Lists all tasks currently managed by the runner and their statuses.

        Returns:
            A dictionary where keys are task IDs and values are their statuses.
        """
        status_dict = {}
        for task_id, task in self._tasks.items():
            status_dict[task_id] = self.get_task_status(task_id)
        return status_dict

    async def stop_all_tasks(self) -> None:
        """
        Stops all currently running tasks.
        """
        print("Stopping all tasks...")
        tasks_to_cancel = list(self._tasks.values()) # Create a copy to avoid modifying during iteration
        for task in tasks_to_cancel:
            if not task.done():
                task.cancel()
        # Wait for all cancellations to be processed
        await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
        print("All tasks stopped.")

    async def remove_all_tasks(self) -> None:
        """
        Removes all tasks from the runner. This will also stop them if they are running.
        """
        print("Removing all tasks...")
        task_ids = list(self._tasks.keys()) # Get keys before modifying the dictionary
        for task_id in task_ids:
            await self.remove_task(task_id)
        print("All tasks removed.")

# --- Example Usage ---

async def sample_task(task_id: str, duration: int):
    """A sample asynchronous task that runs for a specified duration."""
    print(f"Task '{task_id}' started, will run for {duration} seconds.")
    try:
        for i in range(duration):
            await asyncio.sleep(1)
            print(f"Task '{task_id}' working... ({i+1}/{duration}s)")
        print(f"Task '{task_id}' finished successfully.")
    except asyncio.CancelledError:
        print(f"Task '{task_id}' was cancelled.")
    except Exception as e:
        print(f"Task '{task_id}' encountered an error: {e}")

async def main():
    runner = AsyncTaskRunner()

    print("--- Adding Tasks ---")
    # Add a few tasks
    task1_id = await runner.add_task(sample_task("MyTask1", 5), task_name="long_running")
    task2_id = await runner.add_task(sample_task("MyTask2", 3), task_name="short_task")
    task3_id = await runner.add_task(sample_task("MyTask3", 7), task_name="another_one")

    print("\n--- Initial Task Status ---")
    print(runner.list_tasks())

    print("\n--- Starting Tasks (they are already scheduled by create_task) ---")
    # For asyncio.create_task, tasks are scheduled immediately.
    # This method is more for conceptual clarity or if you had a different task creation mechanism.
    await runner.start_task(task1_id)
    await runner.start_task(task2_id)
    await runner.start_task(task3_id)

    # Give tasks a moment to start
    await asyncio.sleep(2)

    print("\n--- Status After a Short Wait ---")
    print(runner.list_tasks())

    print("\n--- Stopping a Task ---")
    await runner.stop_task(task2_id)

    print("\n--- Status After Stopping Task 2 ---")
    print(runner.list_tasks())

    print("\n--- Adding Another Task Dynamically ---")
    task4_id = await runner.add_task(sample_task("MyTask4", 4), task_name="new_task")

    print("\n--- Status After Adding Task 4 ---")
    print(runner.list_tasks())

    print("\n--- Removing a Task ---")
    await runner.remove_task(task3_id) # This will also stop it if running

    print("\n--- Status After Removing Task 3 ---")
    print(runner.list_tasks())

    print("\n--- Waiting for remaining tasks to complete ---")
    # We need to wait for the event loop to finish tasks that are still running.
    # A simple way is to await all tasks that are still in the _tasks dictionary.
    # Or, we can just let the program run its course if it's a standalone script.
    # For a more controlled shutdown, you might want to explicitly await tasks.
    await asyncio.sleep(5) # Give task1 and task4 time to finish

    print("\n--- Final Status ---")
    print(runner.list_tasks())

    print("\n--- Stopping All Remaining Tasks ---")
    await runner.stop_all_tasks()

    print("\n--- Status After Stopping All ---")
    print(runner.list_tasks())

    print("\n--- Removing All Tasks ---")
    await runner.remove_all_tasks()

    print("\n--- Final Status After Removing All ---")
    print(runner.list_tasks())

if __name__ == "__main__":
    # To run async code, we need an event loop
    asyncio.run(main())
