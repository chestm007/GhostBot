import logging
from typing import List

import pymem
from pymem.exception import CouldNotOpenProcess


class PymemProcess:
    @staticmethod
    def get_proc_matching(match: bytes):
        for p in pymem.process.list_processes():
            if p.szExeFile == match:
                try:
                    yield pymem.Pymem(p.th32ProcessID)
                except CouldNotOpenProcess:
                    pymem.logger.info("could not open process (%s), maybe it hasnt logged in yet, "
                                      "or is running as Administrator? skipping...", p.th32ProcessID)

    @classmethod
    def list_clients(cls) -> List[pymem.Pymem]:
        pymem.logger.setLevel(logging.INFO)
        return list(cls.get_proc_matching(b'client.exe'))


    @classmethod
    def get_game_exe(cls, auto_cleanup: bool = False) -> pymem.Pymem:
        games = list(cls.get_proc_matching(b'game.exe'))
        if len(games) > 1:
            if not auto_cleanup:
                raise KeyError()

            from GhostBot.client_launcher import ClientLauncher
            for game in games[:2]:
                ClientLauncher(game).close_window()
                games.remove(game)


        if len(games) == 1:
            return games.pop()
        else:
            raise IndexError
