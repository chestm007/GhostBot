import sys

from GhostBot.controller.async_bot_controller import main as async_bot_controller_main
from GhostBot.UX.main import main as ux_main

if __name__ == "__main__":
    match sys.argv[1]:
        case '--server': async_bot_controller_main()
        case '--client': ux_main()