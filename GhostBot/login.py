import os
import time

import win32api

from GhostBot.client_window import ClientWindow
from GhostBot.lib.win32.process import PymemProcess


class ClientLauncher(ClientWindow):
    path = 'E:\\TalismanOnline'
    path = 'C:\Program Files (x86)\TalismanOnline'
    exe = 'game.exe'
    orig_dir = os.getcwd()

    def __init__(self):
        self.launch()
        proc = PymemProcess.get_game_exe()
        super().__init__(proc)

    def launch(self):
        os.chdir(self.path)
        self._ = win32api.WinExec(f'{self.path}\\{self.exe}')
        os.chdir(self.orig_dir)
        return self


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
        return {proc.process_id: proc for proc in PymemProcess.list_clients()}

    seen_clients = list_clients()
    print(seen_clients.values())
    c = ClientLauncher()
    time.sleep(1)
    c.left_click((480, 335))  # Genesis
    time.sleep(1.5)
    c.left_click((480, 455))  # Enter Game
    time.sleep(6)

    for cl, p in list_clients().items():
        if cl not in seen_clients.keys():
            print(c, p)
            try:
                print('attempting to get window')
                c = ClientWindow(p)
                time.sleep(5)
            except Exception:
                time.sleep(2)
                try:
                    print('attempting to get window')
                    c = ClientWindow(p)
                    time.sleep(3)
                except Exception:
                    print('failed')
                    return
                print('entering username')
            c.type_keys(username)
            c.press_key('tab')
            print('entering password')
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
