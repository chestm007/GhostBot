from __future__ import annotations

import contextlib
import json
from typing import TYPE_CHECKING, Any, Callable

from GhostBot.IPC.client import IPCClient
from GhostBot.IPC.server import IPCServer
from GhostBot.config import Config, ConfigLoader
from GhostBot.IPC.message import Message, Command
from GhostBot.config import LoginDetailsConfigLoader

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotController, BotClientWindow


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
        _dispatch_map: dict[Command, Callable[[Message], Message | bool | None]] = dict()

        def _dispatch_start(_message: Message):
            self.logger.debug("dispatching START")
            self.bot_controller.start_bot(_message.target)
            return _message
        _dispatch_map[Command.START] = _dispatch_start

        def _dispatch_stop(_message: Message):
            self.logger.debug("dispatching STOP")
            self.bot_controller.stop_bot(_message.target)
            return _message
        _dispatch_map[Command.STOP] = _dispatch_stop

        def _dispatch_info(_message: Message):
            self.vdebug("dispatching INFO")
            return self.bot_controller_clients_message
        _dispatch_map[Command.INFO] = _dispatch_info

        def _dispatch_info_char(_message: Message):
            self.vdebug("dispatching INFO_CHAR")
            if _message.target:
                self.vdebug("dispatching INFO containing for [%s]", _message.target)
                _target = self.bot_controller.get_client(_message.target)
                if _target:
                    return Message(Command.INFO_CHAR, _target.to_json())
                return
        _dispatch_map[Command.INFO_CHAR] = _dispatch_info_char

        def _dispatch_info_autologin(_message: Message):
            self.vdebug("dispatching INFO_AUTOLOGIN")
            return Message(Command.INFO_AUTOLOGIN, ' '.join(self.bot_controller.login_config.chars.keys()))
        _dispatch_map[Command.INFO_AUTOLOGIN] = _dispatch_info_autologin

        def _dispatch_config_get(_message: Message):
            self.logger.info("dispatching CONFIG get")
            _client: BotClientWindow = self.bot_controller.get_client(_message.target['char'])
            if not _client:
                self.logger.info('char: %s - not found', _message.target['char'])
                return
            if _client.config is None:
                _client.load_config()
                if _client.config is None:
                    self.logger.error('client config not found for %s', _message.target['char'])
                    return
            return Message(Command.CONFIG_GET, json.dumps(_client.config.to_yaml()))
        _dispatch_map[Command.CONFIG_GET] = _dispatch_config_get

        def _dispatch_config_autologin_get(_message: Message):
            self.logger.info("dispatching CONFIG_AUTOLOGIN_GET")
            _config = self.bot_controller.login_config.get(_message.target['char'])
            if _config:
                return Message(Command.CONFIG_AUTOLOGIN_GET, json.dumps(_config.__dict__))
            self.logger.info('autologin config not found for %s', _message.target['char'])
            return Message(Command.CONFIG_AUTOLOGIN_GET, json.dumps({}))
        _dispatch_map[Command.CONFIG_AUTOLOGIN_GET] = _dispatch_config_autologin_get

        def _dispatch_config_set(_message: Message):
            self.vdebug("dispatching CONFIG set")
            _client: BotClientWindow = self.bot_controller.get_client(_message.target['char'])
            if _client is not None:
                self.vdebug("Setting config for %s", _client.name)
                conf = Config.load_yaml(_message.target.get('config'))
                self.logger.info("char: %s - set config: %s", _client.name, conf)
                ConfigLoader(_client).save(conf)
                _client.set_config(conf)
                return _message
            self.logger.info('char: %s - not found', _message.target['char'])
            return False
        _dispatch_map[Command.CONFIG_SET] = _dispatch_config_set

        def _dispatch_config_autologin_set(_message: Message):
            self.logger.info("dispatching CONFIG_AUTOLOGIN_SET")
            _conf_yaml = _message.target
            _char_autologin_config = LoginDetailsConfigLoader.CharDetails(**_conf_yaml)
            self.bot_controller.login_config.chars[_char_autologin_config.char_name] = _char_autologin_config
            LoginDetailsConfigLoader().save(self.bot_controller.login_config)
            return _message
        _dispatch_map[Command.CONFIG_AUTOLOGIN_SET] = _dispatch_config_autologin_set

        def _dispatch_config_autologin_delete(_message: Message):
            self.logger.info("dispatching CONFIG_AUTOLOGIN_DELETE")
            del self.bot_controller.login_config.chars[_message.target['char']]
            LoginDetailsConfigLoader().save(self.bot_controller.login_config)
            return _message
        _dispatch_map[Command.CONFIG_AUTOLOGIN_DELETE] = _dispatch_config_autologin_delete

        def _dispatch_open_client(_message: Message):
            self.logger.info("dispatching OPEN_CLIENT")
            self.bot_controller.requested_logins.append(_message.target['char'])
            return _message
        _dispatch_map[Command.OPEN_CLIENT] = _dispatch_open_client

        def _dispatch_close_client(_message: Message):
            self.logger.info("dispatching CLOSE_CLIENT")
            _client = self.bot_controller.get_client(_message.target['char'])
            if _client is not None:
                _client.close_window()
                return _message
            self.logger.info('char: %s - not found', _message.target['char'])
            return False
        _dispatch_map[Command.CLOSE_CLIENT] = _dispatch_close_client

        self.vdebug('dispatching %s', _data)
        for message in Message.from_json_handling_multiple(_data):
            if not message:
                self.logger.debug('empty message')
                continue
            self.logger.debug("dispatching message: %s", message)
            result = _dispatch_map.get(message.command)(message)
            if isinstance(result, Message):
                pass
            elif isinstance(result, bool):
                result = str(result)
            else:
                result = None
            try:
                conn.sendall(result.encode('utf8'))
            except Exception as e:
                self.logger.exception(e)


class GhostbotIPCClient(IPCClient):
    def __init__(self, host: str = 'localhost', port: int = 64057):
        super().__init__(host=host, port=port)
        self._callbacks: dict[Command, list[Callable[[Message], Any]]] = {command: [] for command in Command.__members__}

    def send(self, data: Message) -> Message:
        try:
            self.logger.debug(f'sending {data}')
            self.send_message(data)
        except ConnectionRefusedError:
            self.logger.error('server offline?')
        except Exception as e:
            self.logger.exception(e)

    def add_callback(self, command: Command, callback: Callable[[Message], Any]):
        self.logger.debug(f'registering callback for {command} to func {callback}')
        self._callbacks[command.name].append(callback)

    def del_callback(self, command: Command, callback: Callable[[Message], Any]):
        self.logger.debug(f'unregistering callback for {command} to func {callback}')
        self._callbacks[command.name].remove(callback)

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
                _callbacks = self._callbacks.get(message.command.name)
                if _callbacks:
                    return all(cb(message) for cb in _callbacks)
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
        return response.target.split(' ') if response else []

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

    def get_config_autologin(self, target: str):
        self.logger.info(f"{self.__class__.__name__}: sending get autologin config message for :{target}")
        self.send(Message(Command.CONFIG_AUTOLOGIN_GET, dict(action="get", char=target)))

    def set_config(self, target: str, config: Config):
        self.logger.info(f"{self.__class__.__name__}: sending set config message for :{target} :: {config}")
        return self.send(Message(Command.CONFIG_SET, dict(action="set",char=target, config=config.to_yaml())))

    def set_config_autologin(self, config: LoginDetailsConfigLoader.CharDetails):
        self.logger.info(f'{self.__class__.__name__}: sending set autologin config message for :{config.char_name}')
        return self.send(Message(Command.CONFIG_AUTOLOGIN_SET, config.__dict__))

    def delete_config_autologin(self, target: str):
        self.logger.info(f"{self.__class__.__name__}: sending delete config autologin message for :{target}")
        return self.send(Message(Command.CONFIG_AUTOLOGIN_DELETE, dict(action="delete", char=target)))

    def list_chars_autologin(self) -> list[str]:
        self.logger.info(f"{self.__class__.__name__}: sending list chars autologin message")
        response = self.send(Message(Command.INFO_AUTOLOGIN))
        return response.target.split(' ') if response else []

    def close_client(self, target: str):
        self.logger.info(f"{self.__class__.__name__}: sending close client message for :{target}")
        return self.send(Message(Command.CLOSE_CLIENT, dict(action='close', char=target)))

    def open_client(self, target: str):
        self.logger.info(f"{self.__class__.__name__}: sending open client message for :{target}")
        return self.send(Message(Command.OPEN_CLIENT, dict(action='open', char=target)))
