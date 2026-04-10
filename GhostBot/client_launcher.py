import asyncio
import os

import pymem
import win32api

from GhostBot.client_window import Win32ClientWindow
from GhostBot.lib.win32.process import PymemProcess


class ClientLauncher(Win32ClientWindow):
    path = 'C:\Program Files (x86)\TalismanOnline'
    exe = 'game.exe'
    orig_dir = os.getcwd()

    def __init__(self, process: pymem.Pymem = None):
        if process:
            super().__init__(process)
        else:
            self.launch()
            proc = PymemProcess.get_game_exe()
            super().__init__(proc)

    def launch(self):
        os.chdir(self.path)
        self._ = win32api.WinExec(f'{self.path}\\{self.exe}')
        os.chdir(self.orig_dir)
        return self

    async def block_until_ready(self):
        await asyncio.sleep(1)
        await self.left_click((480, 335))  # Genesis
        await asyncio.sleep(1.5)
        await self.left_click((480, 455))  # Enter Game
        await asyncio.sleep(6)


if __name__ == "__main__":
    asyncio.run(ClientLauncher().block_until_ready())