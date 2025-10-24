import json
from enum import Enum


class Command(Enum):
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
        return None

class Message:
    def __init__(self, command: str | Command, target: str | dict = None):
        if isinstance(command, Command):
            self.command = command
        else:
            self.command = Command.from_str(command)

        self.target: str | dict = target

    def __str__(self):
        return json.dumps(dict(command=self.command.name.lower(), target=self.target))

    def encode(self, inp: str) -> bytes:
        return str(self).encode(inp)

    @classmethod
    def from_json(cls, data: str) -> "Message | None":
        print(data)
        return cls(**json.loads(data))

if __name__ == '__main__':
    message = Message('exit')
    print(message)
    print(Message.from_json('{"command": "start", "target": "iSuckYouDry"}').__dict__)