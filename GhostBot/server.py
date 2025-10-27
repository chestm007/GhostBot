from __future__ import annotations

import json
import pickle
import socket
from typing import TYPE_CHECKING

from GhostBot import logger
from GhostBot.config import Config, ConfigLoader
from GhostBot.rpc.message import Message, Command

if TYPE_CHECKING:
    from GhostBot.bot_controller import BotController


class GhostbotIPCServer:
    def __init__(self, bot_controller: BotController, host: str | None = None, port: int = None):
        self.host = host or ''
        self.port = port or 64057
        self.bot_controller = bot_controller

    def listen(self):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, self.port))
                    s.listen(1)
                    conn, addr = s.accept()
                    with conn:
                        #data = Message.from_json(conn.recv(1024).decode('utf-8'))
                        data = pickle.loads(conn.recv(1024))
                        if data.command == Command.EXIT:
                            logger.debug(f'exit command received')
                            return
                        result = self.dispatch(data)
                        conn.sendall(pickle.dumps(result))
            except KeyboardInterrupt:
                logger.info('exiting')
                break
            except Exception as e:
                logger.exception(e)

    def dispatch(self, message: Message) -> Message | bool | None:
        match message.command:
            case Command.START:
                self.bot_controller.start_bot(message.target)
                return message
            case Command.STOP:
                self.bot_controller.stop_bot(message.target)
                return message
            case Command.INFO:
                if message.target:
                    return Message(Command.INFO, self.bot_controller.get_client(message.target).to_json())
                return Message(Command.INFO, ' '.join(self.bot_controller.client_keys))
            case Command.CONFIG:
                match message.target.get('action'):
                    case "get":
                        return Message(Command.CONFIG, json.dumps(self.bot_controller.get_client(message.target['char']).config.to_yaml()))
                    case "set":
                        _client = self.bot_controller.get_client(message.target['char'])
                        if _client is not None:
                            logger.info(f"Setting config for {_client.name}")
                            conf = Config.load_yaml(message.target.get('config'))
                            logger.debug(f'set config: {conf}')
                            ConfigLoader(_client).save(conf)
                            _client.set_config(conf)
                            return message
                        return False

        return None


class IPCClient:
    def __init__(self, host: str = '127.0.0.1', port: int = 64057):
        self.host = host
        self.port = port

    def send(self, data: Message) -> Message:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            #s.sendall(data.encode('utf-8'))
            s.sendall(pickle.dumps(data))
            recv = s.recv(1024)
            return pickle.loads(recv)

    def shutdown_server(self):
        return self.send(Message(Command.EXIT))

    def list_chars(self) -> list[str]:
        return self.send(Message(Command.INFO)).target.split(' ')

    def start_bot(self, target: str):
        return bool(self.send(Message(Command.START, target)))

    def stop_bot(self, target: str):
        return bool(self.send(Message(Command.STOP, target)))

    def char_info(self, target: str):
        return self.send(Message(Command.INFO, target))

    def get_config(self, target: str):
        _config = self.send(Message(Command.CONFIG, dict(action="get", char=target))).target
        return Config.load_yaml(
            json.loads(
                _config
            )
        )

    def set_config(self, target: str, config: Config):
        return self.send(Message(Command.CONFIG, dict(action="set",char=target, config=config.to_yaml())))


if __name__ == '__main__':
    client = IPCClient()
    client.start_bot("iSuckYouDry")
    #client.send(Message(Command.START, "FukMeWithNoLube"))
    #client.send(Message(Command.EXIT))
    #print(client.send(Message(Command.INFO, 'Ch35TY17')))
    #client.send(Message(Command.EXIT))