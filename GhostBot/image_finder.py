from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    from GhostBot.client_window import ClientWindow


class ImageFinder:
    image_folder = os.path.join(os.path.curdir, "Images", "SELL")
    misc_folder = os.path.join(os.path.curdir, "Images", "misc")
    items = {}

    for filename in os.listdir(image_folder):
        fullpath = os.path.join(image_folder, filename)
        if (image := cv2.imread(fullpath, cv2.IMREAD_GRAYSCALE)) is not None:
            items[filename] = image


    @classmethod
    def find_image_in_window(cls, target_image, client: ClientWindow, threshold=0.8):
        """
        Find the passed in image in the client window and return the coordinates to it.

        :return: coordinates for the ``target_image`` passed in
        """

        window_img = client.capture_window()
        # Locate image in the screen capture
        result = cv2.matchTemplate(window_img, target_image, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > threshold:  # Adjust as needed. lower = more matches
            return max_loc[0], max_loc[1] - 30

        return None

    def find_items_in_window(self, item_images):
        to_delete = []

        tolerance = 3  # Tolerância em pixels para coordenadas duplicadas

        window_img = self._client.capture_window()
        #window_gray = cv2.cvtColor(window_img, cv2.COLOR_BGR2GRAY)

        for offset in self._get_bag_coords():
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

    @classmethod
    def _get_destroy_item_location(cls, client: ClientWindow) -> tuple[int, int] | None:
        destroy_path = "Images/misc/destroy-item.bmp"
        destroy_image = cv2.imread(destroy_path, cv2.IMREAD_GRAYSCALE)
        try:
            coordinates = cls.find_image_in_window(destroy_image, client)
        except cv2.error as e:
            print(e)
            coordinates = None

        return coordinates or None

    @classmethod
    def _get_dialog_ok_location(cls, client: ClientWindow) -> tuple[int, int] | None:
        _path = "Images/misc/dialog_ok.bmp"
        _image = cv2.imread(_path, cv2.IMREAD_GRAYSCALE)
        try:
            coordinates = cls.find_image_in_window(_image, client, threshold=0.6)
        except cv2.error as e:
            print(e)
            coordinates = None

        return coordinates or None

    def __init__(self, client: ClientWindow):
        self._client = client
        self._destroy_item_location: tuple[int, tuple[int, int]] = None

    @property
    def destroy_item_location(self) -> tuple[int, int]:
        if self._destroy_item_location is None or time.time() - self._destroy_item_location[0] > 6000:
            self._destroy_item_location = (time.time(), self._get_destroy_item_location(self._client))
        return self._destroy_item_location[1]

    def _get_bag_coords(self):
        destroy_x, destroy_y = self.destroy_item_location

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