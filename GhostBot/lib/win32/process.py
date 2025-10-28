from typing import List

import pymem

class PymemProcess:
    @staticmethod
    def list_clients() -> List[pymem.Pymem]:
        return [pymem.Pymem(p.th32ProcessID) for p in pymem.process.list_processes() if p.szExeFile == b'client.exe']


    @staticmethod
    def get_game_exe() -> pymem.Pymem:
        games = [pymem.Pymem(p.th32ProcessID) for p in pymem.process.list_processes() if p.szExeFile == b'game.exe']
        if len(games) == 1:
            return games.pop()
        raise Exception

