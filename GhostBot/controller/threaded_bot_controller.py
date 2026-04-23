import threading
import time
from typing import Callable

from GhostBot.client_launcher import ClientLauncher
from GhostBot.controller.bot_controller import BotController, BotClientWindow
from GhostBot.controller.login_controller import LoginController
from GhostBot.enums.bot_status import BotStatus
from GhostBot.lib.win32.process import PymemProcess


class ThreadedBotController(BotController):
    def __init__(self, auto_login: bool = True, **kwargs):
        super().__init__(**kwargs)
        self._tasks: dict[str, threading.Thread] = dict()
        self.auto_login = auto_login

    def scan_for_clients(self):
        try:
            while self._running:
                self.logger.debug("uptime %ss", self._total_running_secs)
                self._remove_closed_pending_clients()
                self._scan_for_clients()

                if self.auto_login:
                    self._process_login_queue()

                for i in range(0, 10):
                    if not self._running:
                        break
                    time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info('Exiting as requested...')
            return
        except Exception as e:
            self.logger.exception(e)
            return

    def _process_login_queue(self):

        def callback(__client, result):
            if not result:
                self.logger.debug('[%s] Login failed, removing %s from self._pending_clients', __client.process_id, __client.name)
                try:
                    self._pending_clients.pop(__client.name)
                except KeyError:
                    self.logger.debug('[%s] pending client not found.. possibly harmless', __client.name)
            else:
                self.logger.debug('[%s] :: Login succeeded', __client.process_id)
                self._pending_clients.pop(__client.name)
                self.add_client(__client)

        eligible_logins = self._eligible_logins()

        if not eligible_logins:
            self.logger.debug('no eligible logins...')
            return

        elif len(self.login_queue) < 1:
            try:
                if len(list(PymemProcess.get_proc_matching(b'game.exe'))) == 0:
                    self.logger.debug('spawning game launcher')
                    ClientLauncher().block_until_ready()
                else:
                    self.logger.debug('game launcher already running')
            except IndexError:
                self.logger.debug('game launcher process didnt launch, retrying')
            except KeyError:
                self.logger.debug('too many game launcher processes detected, there can only be one')

        for pid, _client in dict(self.login_queue).items():

            if f"task{pid}" not in self._tasks.keys():
                lc = LoginController(_client, self)

                if lc.current_stage == LoginController.LoginStage.character_select:
                    time.sleep(5)  # fixes a race condition with the client window opening

                __char = _client.get_window_name()

                self.logger.debug('self._eligible_logins :: %s', eligible_logins)

                if __char in eligible_logins and _client.name is None:
                    _conf = eligible_logins.pop(__char)
                    self.logger.info('[%s|%s] resuming login procedure with config %s', pid, _conf.char_name, _conf)
                elif lc.current_stage == LoginController.LoginStage.enter_credentials:
                    __char, _conf = eligible_logins.popitem()
                    self.logger.info('[%s|%s] starting login procedure with config %s', pid, _conf.char_name, _conf)
                else:
                    self.logger.info('[%s|%s] skipping', pid, __char)
                    continue

                if __char in self.requested_logins:
                    self.requested_logins.remove(__char)

                self._pending_clients[_conf.char_name] = _client

                self.logger.debug('LoginStage of new pending client :: %s', lc.current_stage)

                # if lc.current_stage == LoginController.LoginStage.enter_credentials:
                self.logger.debug('[%s|%s] setting config for LoginController', pid, _conf.char_name)
                lc.set_config(_conf)
                self._add_task(lc.handle_login, f"task{pid}", lambda result: callback(_client, result))
                del self.login_queue[pid]

    def _remove_closed_pending_clients(self):
        current_running_procs = self._pymem_process.list_clients()
        for k, v in list(self._pending_clients.items()):
            if (c_pid := v.proc.process_id) not in (p.process_id for p in current_running_procs):
                self.logger.info("BotController :: removing [%s]", c_pid)
                try:
                    self._stop_task(f'task{self._pending_clients.pop(k).process_id}')
                except Exception as e:
                    self.logger.info(e)

    def _add_task(self, target: Callable, task_name: str, *target_args, **target_kwargs):
        task = threading.Thread(target=target, args=target_args, kwargs=target_kwargs)
        self._tasks[task_name] = task
        task.start()

    def _stop_task(self, task_name: str, timeout: int = 30):
        self._tasks.get(task_name).join(timeout=timeout)

    def _stop_all_tasks(self, timeout: int = 30):
        for _task_name, _task in self._tasks.items():
            self.logger.info('stopping task %s', _task_name)
            _task.join(timeout=timeout)

    def start_bot(self, client: BotClientWindow | str) -> None:
        if isinstance(client, str):
            _client = client
            if (client := self.get_client(client)) is None:
                self.logger.warning('no client %s', _client)
                return
        self.reload_bot_config(client)
        client.start_bot()
        self._add_task(self._run_bot, client.name, client)

    def _run_bot(self, client: BotClientWindow) -> None:
        client.bot_status = BotStatus.started
        self.logger.info("%s: Started.", client.name)

        functions = list(self._get_functions_for_client(client))
        for function in functions:
            if self._ipc_log_handler not in function.logger.handlers:
                function.logger.addHandler(self._ipc_log_handler)

        while client.running:
            client.bot_status = BotStatus.running
            if client.disconnected:
                self.logger.info("%s: disconnected.", client.name)
                client.close_window()
                break
            try:
                for function in functions:
                    function.run()

            except Exception as e:
                self.logger.exception(e)
        client.bot_status = BotStatus.stopped
        self.logger.info("%s: Stopped.", client.name)

    def stop_all_bots(self, timeout=30) -> None:
        self.logger.info("stopping all bots...")
        _stopping = []
        for client in self.clients.values():
            if client.running:
                self.logger.info('stopping client  %s', client.name)
                client.stop_bot()
                _stopping.append(client)
        for client in _stopping:
            self.logger.debug('joining thread %s', client.name)
            self._stop_task(client.name, timeout)
            client.bot_status = BotStatus.stopped

    def stop_bot(self, client: str | BotClientWindow, timeout=5) -> None:
        if isinstance(client, str):
            client: BotClientWindow = self.get_client(client)
            if client is None:
                self.logger.warning('no client %s', client)
                return

        if client.running:
            client.stop_bot()
            self._stop_task(client.name, timeout)
            client.bot_status = BotStatus.stopped

    def listen(self):
        self._running = True
        try:
            self._controller_start_time = time.time()
            self._add_task(self.scan_for_clients, "scan_for_clients")
            self.server.run()
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info('Exiting...')
        except Exception as e:
            self.logger.exception(e)
        self.shutdown()

    def shutdown(self):
        super().shutdown()
        self._stop_all_tasks()

if __name__ == '__main__':
    import os
    import logging
    from GhostBot import logger as _logger

    if os.environ.get('PYCHARM_HOSTED'):
        _logger.setLevel(logging.DEBUG)

    bot_controller = ThreadedBotController()
    try:
        bot_controller.listen()
    except KeyboardInterrupt:
        _logger.info('received signal, exiting')
    finally:
        _logger.info('exiting...')
        bot_controller.shutdown()