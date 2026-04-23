import json
from enum import Enum, unique
from json import JSONDecodeError
from typing import Generator

from GhostBot import logger


@unique
class Command(Enum):
    ERROR = -2
    EXIT = -1
    INFO = 1
    INFO_CHAR = 2
    INFO_AUTOLOGIN = 3
    START = 10
    STOP = 20
    CONFIG = 30
    CONFIG_GET = 31
    CONFIG_SET = 32
    CONFIG_AUTOLOGIN_GET = 33
    CONFIG_AUTOLOGIN_SET = 34
    CONFIG_AUTOLOGIN_DELETE = 35
    OPEN_CLIENT = 40
    CLOSE_CLIENT = 41
    LOG = 100
    SERVER_HEARTBEAT = 200

    @classmethod
    def from_str(cls, command: str) -> "Command | None":
        return cls.__members__.get(command.upper())

    def encode(self, inp):
        return str(self.value).encode(inp)

    @classmethod
    def from_value(cls, value):
        return cls(int(value))

class Message:
    def __init__(self, command: str | Command, target: str | dict = None):
        if isinstance(command, Command):
            self.command = command
        else:
            self.command = Command.from_str(command)

        self.target: str | dict = target

    def __str__(self):
        try:
            return json.dumps(dict(command=self.command.name.lower(), target=self.target))
        except (TypeError, AttributeError) as e:
            logger.error(f"{self.__class__.__name__}: Error converting Message to string: {self.__dict__}")
            raise e

    def encode(self, inp: str) -> bytes:
        return str(self).encode(inp)

    @classmethod
    def from_json(cls, data: str) -> 'Message':
        try:
            return cls(**json.loads(data))
        except JSONDecodeError as e:
            logger.error(f"Error decoding message to JSON: message: type({type(data)} [{data}]")
            logger.exception(e)

    @classmethod
    def from_json_handling_multiple(cls, data: str) -> Generator['Message', None, None]:
        yield from (cls.from_json(n) for n in data.replace('}{', '}<<>>{').split('<<>>'))

if __name__ == '__main__':
    message = Message('exit')
    print(message)
    print(Message.from_json('{"command": "start", "target": "iSuckYouDry"}').__dict__)