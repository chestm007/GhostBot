import logging
import threading
import time
from typing import Callable

from GhostBot import logger
from GhostBot.client_launcher import ClientLauncher
from GhostBot.controller.bot_controller import BotController, BotClientWindow
from GhostBot.controller.login_controller import LoginController
from GhostBot.enums.bot_status import BotStatus
from GhostBot.server import GhostbotIPCServer


class ThreadedBotController(BotController):
    def __init__(self):
        super().__init__()
        self._tasks: dict[str, threading.Thread] = dict()
        self._running = False

    def scan_for_clients(self):
        try:
            while self._running:
                logger.debug("AsyncBotController :: uptime %ss", self._total_running_secs)
                self._remove_closed_pending_clients()
                self._scan_for_clients()
                self._process_login_queue()
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info(f'AsyncBotController :: Exiting as requested...')
            return
        except Exception as e:
            logger.exception(e)
            return

    def _process_login_queue(self):

        def callback(__client, result):
            if not result:
                logger.debug('AsyncBotController :: [%s] Login failed, removing %s from self._pending_clients', __client.process_id, __client.name)
                try:
                    self._pending_clients.pop(__client.name)
                except KeyError:
                    logger.debug('AsyncBotController :: [%s] pending client not found.. possibly harmless', __client.name)
            else:
                logger.debug('AsyncBotController :: [%s] :: Login succeeded', __client.process_id)
                self._pending_clients.pop(__client.name)
                self.add_client(__client)

        if not self._eligible_logins():
            return

        elif len(self.login_queue) < 1:
            try:
                ClientLauncher().block_until_ready()
            except IndexError:
                logger.debug('AsyncBotController :: game launcher process didnt launch, retrying')
            except KeyError:
                logger.debug('AsyncBotController :: too many game launcher processes detected, there can only be one')

        for pid, _client in dict(self.login_queue).items():

            if f"task{pid}" not in self._tasks.keys():
                lc = LoginController(_client)

                if lc.current_stage == LoginController.LoginStage.character_select:
                    time.sleep(5)  # fixes a race condition with the client window opening

                char = _client.get_window_name()

                logger.debug('AsyncBotController :: self._eligible_logins :: %s', self._eligible_logins())

                if char in self._eligible_logins().keys() and _client.name is None:
                    _conf = (char, self._eligible_logins().pop(char))
                    logger.debug('AsyncBotController :: [%s|%s] resuming login procedure with config %s', pid, char, _conf)
                elif lc.current_stage == LoginController.LoginStage.enter_credentials:
                    _conf = self._eligible_logins().popitem()
                    logger.debug('AsyncBotController :: [%s|%s] starting login procedure with config %s', pid, char, _conf)
                    char = _conf[0]
                else:
                    logger.debug('AsyncBotController :: [%s|%s] skipping', pid, char)
                    continue

                self._pending_clients[char] = _client

                logger.debug('AsyncBotController :: LoginStage of new pending client :: %s', lc.current_stage)

                # if lc.current_stage == LoginController.LoginStage.enter_credentials:
                logger.debug('AsyncBotController :: [%s|%s] setting config for LoginController', pid, char)
                lc.set_config(_conf)
                self._add_task(lc.handle_login, f"task{pid}", lambda result: callback(_client, result))
                del self.login_queue[pid]

    def _remove_closed_pending_clients(self):
        current_running_procs = self._pymem_process.list_clients()
        for k, v in list(self._pending_clients.items()):
            if (c_pid := v.proc.process_id) not in (p.process_id for p in current_running_procs):
                logger.info("BotController :: removing [%s]", c_pid)
                try:
                    self._stop_task(f'task{self._pending_clients.pop(k).process_id}')
                except Exception as e:
                    logger.info(e)

    def _add_task(self, target: Callable, task_name: str, *target_args, **target_kwargs):
        task = threading.Thread(target=target, args=target_args, kwargs=target_kwargs)
        self._tasks[task_name] = task
        task.start()

    def _stop_task(self, task_name: str, timeout: int = 30):
        self._tasks.get(task_name).join(timeout=timeout)

    def _stop_all_tasks(self, timeout: int = 30):
        for _task_name, _task in self._tasks.items():
            logger.info('ThreadedBotController :: stopping task %s', _task_name)
            _task.join(timeout=timeout)

    def start_bot(self, client: BotClientWindow | str) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                logger.warning(f'no client {client}')
                return
        self.reload_bot_config(client)
        client.start_bot()
        self._add_task(self._run_bot, client.name, client)

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
            self._stop_task(client.name, timeout)
            client.bot_status = BotStatus.stopped

    def stop_bot(self, client: str | BotClientWindow, timeout=5) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                logger.warning(f'no client {client}')
                return
        if client.running:
            client.stop_bot()
            self._stop_task(client.name, timeout)
            client.bot_status = BotStatus.stopped

    def listen(self, host=None, port=None):
        self._running = True
        try:
            self._controller_start_time = time.time()
            self._add_task(self.scan_for_clients, "scan_for_clients")
            server = GhostbotIPCServer(bot_controller=self, host=host, port=port)
            server.listen()
        except KeyboardInterrupt:
            logger.info('AsyncBotController :: Exiting...')
        except Exception as e:
            logger.exception(e)
        self.stop_all_bots()
        self._stop_all_tasks()

    def shutdown(self):
        self._running = False
        self.stop_all_bots(5)

if __name__ == '__main__':
    import os

    if os.environ.get('PYCHARM_HOSTED'):
        logger.setLevel(logging.DEBUG)

    bot_controller = ThreadedBotController()
    try:
        bot_controller.listen()
    except KeyboardInterrupt:
        logger.info('received signal, exiting')
    finally:
        logger.info('exiting...')
        bot_controller.shutdown()