import os

import pymem
import win32api


class ClientLauncher:
    path = 'E:\\TalismanOnline'
    exe = 'game.exe'
    orig_dir = os.getcwd()

    def _launch(self):
        os.chdir(self.path)
        win32api.WinExec(f'{self.path}\\{self.exe}')
        os.chdir(self.orig_dir)

    @staticmethod
    def _list_clients():
        return [proc for proc in pymem.process.list_processes() if proc.szExeFile == b'client.exe']


def main():
    procs = [proc.th32ProcessID for proc in ClientLauncher._list_clients()]
    print(procs)
    ClientLauncher()._launch()  # works, just cant find the right process after launch now
    new_proc = [proc.th32ProcessID for proc in ClientLauncher()._list_clients() if proc.th32ProcessID not in procs]
    print(new_proc)

if __name__ == "__main__":
    main()
