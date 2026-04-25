# nuitka-project: --include-data-dir=src/GhostBot/Images=Images
# nuitka-project: --include-module=GhostBot

import os

def test_images_found():
    _path_base = os.path.dirname(__file__)
    # if "NUITKA_ONEFILE_DIRECTORY" in os.environ:
    #     print('detected running compiled binary')
    #     _path_base = os.path.join(_path_base, "GhostBot")


    print(_path_base)

    image_folder = os.path.join(_path_base, "Images", "SELL")
    misc_folder = os.path.join(_path_base, "Images", "misc")

    print(image_folder)
    print(misc_folder)

    assert 'dialog_ok.bmp' in os.listdir(misc_folder)
    assert 'greenid.bmp' in os.listdir(image_folder)

test_images_found()
