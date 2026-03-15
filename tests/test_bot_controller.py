from typing import List

import pymem

from GhostBot.bot_controller import BotController
from GhostBot.lib.win32.process import PymemProcess


class MockPymem(pymem.Pymem):
    pass

class MockPymemProcess(PymemProcess):

    @staticmethod
    def list_clients() -> List[pymem.Pymem]:
        return [MockPymem()]

def test_list_clients():
    BotController._pymem_process = MockPymemProcess()
    bot_controller = BotController()