# nuitka-project: --enable-plugin=tk-inter
# nuitka-project: --include-data-dir=src/GhostBot/Images=GhostBot/Images
# nuitka-project: --include-module=GhostBot
# nuitka-project: --windows-console-mode=attach

from GhostBot.UX.main import main

if __name__ == "__main__":
    main()
