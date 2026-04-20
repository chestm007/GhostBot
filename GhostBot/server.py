from __future__ import annotations

import contextlib
import json
from typing import TYPE_CHECKING, Any, Callable

from GhostBot.IPC.client import IPCClient
from GhostBot.IPC.server import IPCServer
from GhostBot.config import Config, ConfigLoader
from GhostBot.IPC.message import Message, Command

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotController
    from controller.bot_controller import BotClientWindow


class GhostbotIPCServer(IPCServer):
    vdebug = lambda msg, *args: None

    def __init__(
        self,
        bot_controller: BotController,
        host: str | None = None,
        port: int | None = None,
        verbose_logging: bool = False
    ):
        super().__init__(host=host or 'localhost', port=port or 64057, heartbeat_interval=10)
        if verbose_logging:
            self.vdebug = self.logger.info
        self.bot_controller = bot_controller

    @property
    def bot_controller_clients_message(self) -> Message:
        return Message(Command.INFO, ' '.join(k for k, v in self.bot_controller.clients.items() if not v.disconnected))

    def accept(self, sock):
        super().accept(sock)
        self.send_to_all(self.bot_controller_clients_message)

    def _dispatch(self, conn, _data: str) -> Message | bool | None:
        self.vdebug('dispatching %s', _data)
        for message in Message.from_json_handling_multiple(_data):
            if not message:
                self.logger.debug('empty message')
                continue
            self.logger.debug("dispatching message: %s", message)
            def _dispatch_message():
                match message.command:
                    case Command.EXIT:
                        self.logger.info(' exit command received')
                        return
                    case Command.START:
                        self.logger.debug("dispatching START")
                        self.bot_controller.start_bot(message.target)
                        return message
                    case Command.STOP:
                        self.logger.debug("dispatching STOP")
                        self.bot_controller.stop_bot(message.target)
                        return message
                    case Command.INFO:
                        self.vdebug("dispatching INFO")
                        return self.bot_controller_clients_message
                    case Command.INFO_CHAR:
                        self.vdebug("dispatching INFO_CHAR")
                        if message.target:
                            self.vdebug("dispatching INFO containing for [%s]", message.target)
                            _target = self.bot_controller.get_client(message.target)
                            if _target:
                                return Message(Command.INFO_CHAR, _target.to_json())
                            return
                    case Command.CONFIG_GET:
                        self.logger.info("dispatching CONFIG get")
                        _client: BotClientWindow = self.bot_controller.get_client(message.target['char'])
                        if _client.config is None:
                            _client.load_config()
                        return Message(Command.CONFIG_GET, json.dumps(_client.config.to_yaml()))
                    case Command.CONFIG_SET:
                        self.vdebug("dispatching CONFIG set")
                        _client: BotClientWindow = self.bot_controller.get_client(message.target['char'])
                        if _client is not None:
                            self.vdebug("Setting config for %s", _client.name)
                            conf = Config.load_yaml(message.target.get('config'))
                            self.logger.info("char: %s - set config: %s", _client.name, conf)
                            ConfigLoader(_client).save(conf)
                            _client.set_config(conf)
                            return message
                        return False

                return None
            try:
                conn.sendall(_dispatch_message().encode('utf8'))
            except Exception as e:
                self.logger.exception(e)


class GhostbotIPCClient(IPCClient):
    def __init__(self, host: str = 'localhost', port: int = 64057):
        super().__init__(host=host, port=port)
        self._callbacks: dict[Command, Callable[[Message], Any]] = {}

    def send(self, data: Message) -> Message:
        try:
            self.logger.debug(f'sending {data}')
            self.send_message(data)
        except ConnectionRefusedError:
            self.logger.error('server offline?')
        except Exception as e:
            self.logger.exception(e)

    def add_callback(self, command: Command, callback: Callable[[Message], Any]):
        self._callbacks[command] = callback

    def _dispatch(self, data: bytes):
        _data = data.decode('utf8')
        with contextlib.suppress(ValueError):
            if Command.from_value(_data) == Command.SERVER_HEARTBEAT:
                self.logger.debug('received HEARTBEAT')
                return
        try:
            for message in Message.from_json_handling_multiple(_data):
                if message is None:
                    self.logger.debug('received empty message')
                    continue
                self.logger.debug(f'dispatching callback for {message}')
                if cb := self._callbacks.get(message.command):
                    return cb(message)
                self.logger.debug('No callback set for %s', message.command)
        except EOFError as e:  # Thrown when server crashes, or is shutdown
            if data.command != Command.EXIT:
                self.logger.exception(e)
                raise e from e
            self.logger.exception(e)
        except Exception as e:
            self.logger.exception(e)
            raise e

    def shutdown_server(self):
        return self.send(Message(Command.EXIT))

    def list_chars(self) -> list[str]:
        self.logger.info(f"{self.__class__.__name__}: sending list chars message")
        response = self.send(Message(Command.INFO))
        if response:
            return response.target.split(' ')
        return []

    def start_bot(self, target: str):
        self.logger.info(f"{self.__class__.__name__}: sending start bot message for :{target}")
        return self.send(Message(Command.START, target))

    def stop_bot(self, target: str):
        self.logger.info(f"{self.__class__.__name__}: sending stop bot message for :{target}")
        return self.send(Message(Command.STOP, target))

    def char_info(self, target: str):
        self.logger.debug(f"{self.__class__.__name__}: sending char info message for :{target}")
        return self.send(Message(Command.INFO_CHAR, target)) or ''

    def get_config(self, target: str):
        self.logger.info(f"{self.__class__.__name__}: sending get config message for :{target}")
        self.send(Message(Command.CONFIG_GET, dict(action="get", char=target)))

    def set_config(self, target: str, config: Config):
        self.logger.info(f"{self.__class__.__name__}: sending set config message for :{target} :: {config}")
        return self.send(Message(Command.CONFIG_SET, dict(action="set",char=target, config=config.to_yaml())))
