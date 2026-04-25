# nuitka-project: --include-data-dir=src/GhostBot/Images=GhostBot/Images

import os
import pathlib

_path_base = pathlib.Path(__file__).parent.resolve()
if "NUITKA_ONEFILE_DIRECTORY" in os.environ:
    _path_base = os.path.join(_path_base, "GhostBot")

def main():
    print(_path_base)
    image_folder = os.path.join(_path_base, "Images", "SELL")
    misc_folder = os.path.join(_path_base, "Images", "misc")
    assert 'dialog_ok.bmp' in os.listdir(misc_folder)
    assert 'greenid.bmp' in os.listdir(image_folder)

if __name__ == "__main__":
    main()

