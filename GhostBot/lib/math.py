import math
from operator import sub

__all__ = ['linear_distance', 'position_difference', 'limit', 'seconds']

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


def seconds(hours=0, minutes=0, seconds=0, tenths=0):
    return (((hours * 60) + minutes) * 60) + seconds + (tenths / 10)
