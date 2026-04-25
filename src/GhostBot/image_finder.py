from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

import cv2
import numpy as np
import pathlib

from GhostBot import logger

if TYPE_CHECKING:
    from GhostBot.abstract_client_window import AbstractClientWindow

_path_base = pathlib.Path(__file__).parent.resolve()
if "NUITKA_ONEFILE_DIRECTORY" in os.environ:
    _path_base = os.path.join(_path_base, "GhostBot")


class ImageFinder:
    image_folder = os.path.join(_path_base, "Images", "SELL")
    misc_folder = os.path.join(_path_base, "Images", "misc")

    if 'dialog_ok.bmp' not in os.listdir(misc_folder):
        raise AssertionError("dialog_ok.bmp not found in misc_folder")
    if 'greenid.bmp' not in os.listdir(image_folder):
        raise AssertionError("greenid.bmp not found in image_folder")

    print("Images path detected...")
    items = {}

    def __init__(self, client: AbstractClientWindow):
        self._client = client
        self._destroy_item_location: tuple[int, tuple[int, int]] = None


    for filename in os.listdir(image_folder):
        fullpath = os.path.join(image_folder, filename)
        if (image := cv2.imread(fullpath, cv2.IMREAD_GRAYSCALE)) is not None:
            items[filename] = image


    def _find_image_in_window(self, target_image, threshold=0.8):
        """
        Find the passed in image in the client window and return the coordinates to it.

        :return: coordinates for the ``target_image`` passed in
        """

        window_img = self._client.capture_window()
        # Locate image in the screen capture
        result = cv2.matchTemplate(window_img, target_image, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > threshold:  # Adjust as needed. lower = more matches
            return max_loc[0], max_loc[1] - 30

        return None

    def find_items_in_window(self, item_images) -> list[tuple[int, int]]:
        to_delete: list[tuple[int, int]] = []

        tolerance = 3  # Tolerância em pixels para coordenadas duplicadas

        window_img = self._client.capture_window()
        #window_gray = cv2.cvtColor(window_img, cv2.COLOR_BGR2GRAY)

        if not (bag_coords := self._get_bag_coords()):
            logger.error("ImageFinder :: _get_bag_coords :: bag_coords returned None")
            return []
        for offset in bag_coords:
            x1, y1, width, height = offset

            bag_area = window_img[y1:y1 + height, x1:x1 + width]

            for item_name, item_image in item_images.items():
                result = cv2.matchTemplate(bag_area, item_image, cv2.TM_CCOEFF_NORMED)
                threshold = 0.9
                loc = np.where(result >= threshold)

                for pt in zip(*loc[::-1]):
                    global_x = x1 + pt[0] + 10
                    global_y = y1 + pt[1] - 15

                    if not any(
                            abs(existing_x - global_x) <= tolerance and abs(existing_y - global_y) <= tolerance for
                            existing_x, existing_y in to_delete):
                        to_delete.append((int(global_x), int(global_y)))

        return to_delete

    def _get_destroy_item_location(self) -> tuple[int, int] | None:
        return self.find_ui_element(os.path.join(self.misc_folder, "destroy-item.bmp"), threshold=0.8)

    @property
    def dialog_ok_location(self) -> tuple[int, int] | None:
        return self.find_ui_element(os.path.join(self.misc_folder, "dialog_ok.bmp"), threshold=0.6)

    def is_map_open(self) -> bool:
        return bool(self.find_ui_element(os.path.join(self.misc_folder, 'map_open.bmp')))

    def _sell_item_npc_location(self, stage=0) -> tuple[int, int] | None:
        stage_path = ['npc_sell', 'item_sell_window_header', 'item_sell']
        return self.find_ui_element(os.path.join(self.misc_folder, f"{stage_path[stage - 1]}.bmp"), threshold=0.62)

    def find_ui_element(self, bitmap_path: str, threshold=0.8) -> tuple[int, int] | None:
        _image = cv2.imread(bitmap_path, cv2.IMREAD_GRAYSCALE)
        try:
            return self._find_image_in_window(_image, threshold=threshold)
        except cv2.error as e:
            logger.error("ImageFinder :: %s :: error in ImageFinder._find_image_in_window", self._client.identifier)
            logger.exception(e)
            return None

    @property
    def destroy_item_location(self) -> tuple[int, int]:
        if self._destroy_item_location is None or time.time() - self._destroy_item_location[0] > 6000:
            self._destroy_item_location = (time.time(), self._get_destroy_item_location())
        return self._destroy_item_location[1]

    def _get_bag_coords(self) -> list[tuple[int, int, int, int]]:
        if (destroy_location := self.destroy_item_location) is None:
            logger.error("ImageFinder :: _get_bag_coords :: destroy_item_location returned None")
            return []
        destroy_x, destroy_y = destroy_location

        bag_cords = [
            (destroy_x - 5, destroy_y - 200, destroy_x + 220, destroy_y - 15),
            (destroy_x + 250, destroy_y - 420, destroy_x + 490, destroy_y - 10),
        ]

        bag_offsets = [
            (destroy_x - 5, destroy_y - 200, destroy_x + 220, destroy_y - 15),
            (destroy_x + 250, destroy_y - 420, destroy_x + 490, destroy_y - 10),
        ]

        bag_images = []
        for x1, y1, x2, y2 in bag_cords:
            bag_img = self._client.capture_window()[y1:y2, x1:x2]
            bag_images.append(bag_img)

        return bag_offsets


if __name__ == "__main__":
    print(ImageFinder.items)