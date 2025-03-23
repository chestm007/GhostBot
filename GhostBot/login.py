import os
import time

import pymem
import win32api

from GhostBot.client_window import ClientWindow


class ClientLauncher(ClientWindow):
    path = 'E:\\TalismanOnline'
    exe = 'game.exe'
    orig_dir = os.getcwd()

    def __init__(self):
        self.launch()
        super().__init__(self.get_game_proc())

    def launch(self):
        os.chdir(self.path)
        self._ = win32api.WinExec(f'{self.path}\\{self.exe}')
        os.chdir(self.orig_dir)
        return self

    @staticmethod
    def list_clients():
        return [proc for proc in pymem.process.list_processes() if proc.szExeFile == b'game.exe']

    @staticmethod
    def get_game_proc():
        procs = [proc for proc in pymem.process.list_processes() if proc.szExeFile == b'game.exe']
        if len(procs) == 1:
            return procs[0]
        raise Exception


class Account:
    chars = [None, None, None]

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def set_char(self, name, index):
        if self.chars[index] is None:
            self.chars[index] = name
            return
        raise IndexError('char already set in acct')

    def get_char(self, name):
        for i, _name in enumerate(self.chars):
            if i == name:
                return i


def main(username, password):
    def list_clients():
        clients = {}
        for proc in pymem.process.list_processes():
            if proc.szExeFile == b'client.exe':
                clients[proc.th32ProcessID] = proc
        return clients

    seen_clients = list_clients()
    c = ClientLauncher()
    time.sleep(0.5)
    c.left_click((480, 335))  # Genesis
    time.sleep(1.5)
    c.left_click((480, 455))  # Enter Game

    #time.sleep(1)


    for cl, p in list_clients().items():
        if cl not in seen_clients.keys():
            print(c, p)
            try:
                c = ClientWindow(p)
                time.sleep(5)
            except Exception:
                time.sleep(2)
                try:
                    c = ClientWindow(p)
                    time.sleep(3)
                except Exception:
                    return
            c.type_keys(username)
            c.press_key('tab')
            c.type_keys(password)
            c.press_key('enter')

            time.sleep(5)
            c.press_key('enter')
            time.sleep(5)

            c.capture_screen()


if __name__ == "__main__":
    main()
    for user, _pass in bots.items():
        input(f'{user}: Starting')
        main(user, _pass)
