import math
from operator import sub

__all__ = ['linear_distance', 'position_difference']
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
