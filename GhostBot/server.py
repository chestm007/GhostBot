from __future__ import annotations

import functools
import json
import socket
from asyncio import Server
from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.config import Config, ConfigLoader
from GhostBot.rpc.message import Message, Command

if TYPE_CHECKING:
    from GhostBot.controller.bot_controller import BotController


class GhostbotIPCServer:
    logger = logger
    vdebug = lambda msg, *args: None

    def __init__(
        self,
        bot_controller: BotController,
        host: str | None = None,
        port: int = None,
        verbose_logging: bool = False
    ):
        if verbose_logging:
            self.vdebug = self.logger.debug
        self.host = host or ''
        self.port = port or 64057
        self.bot_controller = bot_controller
        self.server: Server | None = None

    def listen(self):
        """
        Start and run the sync version of the IPC Server until requested to stop.
        """
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, self.port))
                    s.listen(1)
                    s.settimeout(1)
                    try:
                        conn, addr = s.accept()
                    except TimeoutError:
                        continue

                    with conn:
                        data = Message.from_json(conn.recv(1024).decode('utf8'))
                        # data = pickle.loads(conn.recv(1024))
                        if data.command == Command.EXIT:
                            logger.info('GhostBotIPCServer ::  exit command received')
                            return
                        result = self._dispatch(data)
                        conn.sendall(result.encode('utf8'))
                        # conn.sendall(pickle.dumps(result))
            except KeyboardInterrupt:
                logger.info("GhostBotIPCServer :: Exiting due to keyboard interrupt")
                break
            except Exception as e:
                logger.exception(e)


    # async def _handle_client(self, reader, writer):
    #     request = None
    #     while request != 'quit':
    #         result = await reader.read(1024)
    #         if reader._eof:
    #             await asyncio.sleep(0.5)
    #             continue
    #         self.vdebug("GhostBotIPCServer :: received data: %s", result)
    #         data = Message.from_json(result.decode('utf8'))
    #         if data.command == Command.EXIT:
    #             logger.info(f'exit command received')
    #             self.server.close()
    #             await self.server.wait_closed()
    #             return
    #         result = await self._dispatch(data)
    #         writer.write(result.encode('utf8'))
    #         self.vdebug("GhostBotIPCServer :: sending data: %s", result)
    #         await writer.drain()
    #     writer.close()
    #
    # async def run_server(self):
    #     logger.info('GhostBotIPCServer :: Starting server...')
    #     self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
    #     async with self.server:
    #         try:
    #             try:
    #                 self.logger.info('GhostBotIPCServer :: Serving forever...')
    #                 await self.server.serve_forever()
    #             except CancelledError:
    #                 return
    #         except KeyboardInterrupt:
    #             self.logger.info("GhostBotIPCServer :: Exiting due to keyboard interrupt")
    #             return
    #         except Exception as e:
    #             logger.exception(e)
    #             return

    def _dispatch(self, message: Message) -> Message | bool | None:
        self.vdebug("GhostBotIPCServer :: dispatching message: %s", message)
        match message.command:
            case Command.START:
                self.logger.debug("GhostBotIPCServer :: dispatching START")
                self.bot_controller.start_bot(message.target)
                return message
            case Command.STOP:
                self.logger.debug("GhostBotIPCServer :: dispatching STOP")
                self.bot_controller.stop_bot(message.target)
                return message
            case Command.INFO:
                self.vdebug("GhostBotIPCServer :: dispatching INFO")
                if message.target:
                    self.vdebug("GhostBotIPCServer :: dispatching INFO containing for [%s]", message.target)
                    return Message(Command.INFO, self.bot_controller.get_client(message.target).to_json())
                return Message(Command.INFO, ' '.join(k for k, v in self.bot_controller.clients.items() if not v.disconnected))
            case Command.CONFIG:
                self.vdebug("GhostBotIPCServer :: dispatching CONFIG")
                match message.target.get('action'):
                    case "get":
                        self.logger.info("GhostBotIPCServer :: dispatching CONFIG get")
                        return Message(Command.CONFIG, json.dumps(self.bot_controller.get_client(message.target['char']).config.to_yaml()))
                    case "set":
                        self.vdebug("GhostBotIPCServer :: dispatching CONFIG set")
                        _client = self.bot_controller.get_client(message.target['char'])
                        if _client is not None:
                            self.vdebug("GhostBotIPCServer :: Setting config for %s", _client.name)
                            conf = Config.load_yaml(message.target.get('config'))
                            self.logger.info("GhostBotIPCServer :: char: %s - set config: %s", _client.name, conf)
                            ConfigLoader(_client).save(conf)
                            _client.set_config(conf)
                            return message
                        return False

        return None


def handle_no_server(func):
    @functools.wraps
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionRefusedError:
            logger.info("Cant connect to Server.")
            return Message(command=Command.ERROR)
    return inner

class IPCClient:
    def __init__(self, host: str = '127.0.0.1', port: int = 64057):
        self.host = host
        self.port = port

    def send(self, data: Message) -> Message:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            #s.sendall(data.encode('utf-8'))
            s.sendall(data.encode('utf8'))
            recv = s.recv(1024)

            try:
                return Message.from_json(recv.decode('utf8'))
            except EOFError as e:  # Thrown when server crashes, or is shutdown
                if data.command != Command.EXIT:
                    raise e from e

    def shutdown_server(self):
        return self.send(Message(Command.EXIT))

    def list_chars(self) -> list[str]:
        logger.info(f"{self.__class__.__name__}: sending list chars message")
        response = self.send(Message(Command.INFO))
        if response:
            return response.target.split(' ')
        return []

    def start_bot(self, target: str):
        logger.info(f"{self.__class__.__name__}: sending start bot message for :{target}")
        return self.send(Message(Command.START, target))

    def stop_bot(self, target: str):
        logger.info(f"{self.__class__.__name__}: sending stop bot message for :{target}")
        return self.send(Message(Command.STOP, target))

    def char_info(self, target: str):
        logger.info(f"{self.__class__.__name__}: sending char info message for :{target}")
        return self.send(Message(Command.INFO, target)) or ''

    def get_config(self, target: str):
        logger.info(f"{self.__class__.__name__}: sending get config message for :{target}")
        _config = self.send(Message(Command.CONFIG, dict(action="get", char=target))).target
        return Config.load_yaml(
            json.loads(_config)
        )

    def set_config(self, target: str, config: Config):
        logger.info(f"{self.__class__.__name__}: sending set config message for :{target} :: {config}")
        return self.send(Message(Command.CONFIG, dict(action="set",char=target, config=config.to_yaml())))

