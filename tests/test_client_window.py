import os.path
import pathlib

import cv2

from GhostBot.client_window import Win32ClientWindow
from GhostBot.image_finder import ImageFinder


class MockClientWindow(Win32ClientWindow):
    _path_base = pathlib.Path(__file__).resolve().parent
    _image = os.path.join(_path_base, "images", 'inventory.bmp')

    def __init__(self, *args, **kwargs):
        pass

    def capture_window(self, color=False):
        return cv2.imread(self._image, cv2.IMREAD_GRAYSCALE)

def test_image_finder_get_destroy_item_location():
    image_finder = ImageFinder(MockClientWindow())
    assert image_finder._get_destroy_item_location()
