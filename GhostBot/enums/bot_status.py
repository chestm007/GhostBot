from enum import Enum


class BotStatus(Enum):
    created = 0
    starting = 1
    started = 2
    running = 3
    stopping = 4
    stopped = 5

