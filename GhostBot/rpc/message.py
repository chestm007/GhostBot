import json
from enum import Enum
from json import JSONDecodeError

from GhostBot import logger


class Command(Enum):
    ERROR = -2
    EXIT = -1
    INFO = 0
    START = 1
    STOP = 2
    CONFIG = 3

    @classmethod
    def from_str(cls, command: str) -> "Command | None":
        match command.upper():
            case 'EXIT': return cls.EXIT
            case 'INFO': return cls.INFO
            case 'START': return cls.START
            case 'STOP': return cls.STOP
            case 'CONFIG': return cls.CONFIG
        return None

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
    def from_json(cls, data: str) -> "Message | None":
        try:
            return cls(**json.loads(data))
        except JSONDecodeError as e:
            logger.error(f"Error decoding message to JSON: message: type({type(data)} {data}")

if __name__ == '__main__':
    message = Message('exit')
    print(message)
    print(Message.from_json('{"command": "start", "target": "iSuckYouDry"}').__dict__)