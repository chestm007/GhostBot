import math
from _operator import add
from operator import sub, mul

__all__ = [
    'linear_distance',
    'position_difference',
    'limit',
    'seconds',
    'item_coordinates_from_pos',
    'coords_to_map_screen_pos'
]

from GhostBot.map_navigation import Zone

# rounds up the position to what the TO client does (its dumb, and wrong, but the games chinese, what do you expect?
pos = lambda a: a*-1 if a < 0 else a


def linear_distance(a: tuple[float, float], b: tuple[float, float]) -> int:
    """
    distance between 2 coordinates in a direct line
    :param a: (x, y)
    :param b: (x, )
    :return: int() representing linear distance
    """
    return math.floor(math.hypot(*map(pos, map(sub, a, b))))


def position_difference(a: tuple[float, float], b: tuple[float, float]) -> map:
    """
    (100, 10) - (70, 7) == (30, 3)
    :param a: (x, y)
    :param b: (x, y)
    :return: (x, y)
    """
    return map(sub, a, b)


def limit(number, _limit):
    if number < 0:
        return _limit * -1 if number < _limit * -1 else number
    else:
        return _limit if number > _limit else number

def coords_to_map_screen_pos(zone: Zone, target_coords: tuple[int, int]) -> tuple[int, int]:
    _diff_x, _diff_y = position_difference(zone.centre, target_coords)
    # FIXME: hardcoded screen size below should be replaced with ClientWindow.get_window_size()
    return int((1024/2) + (_diff_x / zone.scale[0])), int((768 / 2) + (_diff_y / zone.scale[1]))

def seconds(hours=0, minutes=0, seconds=0, tenths=0):
    return (((hours * 60) + minutes) * 60) + seconds + (tenths / 10)


def item_coordinates_from_pos(pos: int, base_pos: tuple[int, int] = None) -> tuple[int, int]:
    multiplier = 35
    _pos = tuple(map(mul, (math.floor(pos/6) , (pos % 6)), (multiplier, multiplier)))
    if base_pos is None:
        return _pos
    else:
        return tuple(map(add, base_pos, _pos))
