import sys
from traceback import print_exception

from GhostBot.client_launcher import ClientLauncher
from GhostBot.controller.bot_controller import BotClientWindow
from GhostBot.controller.login_controller import LoginController
from GhostBot.lib.talisman_ui_locations import UI_locations


def autologin(char_name: str, username: str, password: str, server: str):
    config = (char_name, dict(username=username, password=password, server=server))

    # launch a new game client
    _client = ClientLauncher()
    _client.block_until_ready()

    def callback(result):
        if result:
            print(f"Login success for {_client.name}")
        else:
            print(f"Login unsuccessful for {_client.name}")

    _login_controller = LoginController(BotClientWindow(_client.proc))
    _login_controller.set_config(config)
    _login_controller.handle_login(callback=callback)

if __name__ == "__main__":
    import time

    _servers = [_sn for _sn in UI_locations.server_select.keys() if _sn != 'ok']
    try:
        args = sys.argv[1:]
        if args[-1] not in _servers:
            raise KeyError
        time.sleep(1)
        autologin(*args)
    except Exception as e:
        print_exception(e)
        print(f'\nError: wrong args passed.\n python .\\autologin.py char_name username pass server_name')
        print(f'where server_name is one of:')
        for _sn in _servers:
            print(f'  {_sn}')