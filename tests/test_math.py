from GhostBot.lib.math import limit, position_difference, seconds, scale_minimap_move_distance


def test_limit_0():
    assert limit(0, 20) == 0


def test_limit_0_20():
    for i in range(1, 20):
        assert limit(i, 20) == i
        assert i > 0


def test_limit_20_400():
    for i in range(20, 400):
        assert limit(i, 20) == 20
        assert i > 0


def test_limit_0_neg20():
    for i in range(-20, -1):
        assert limit(i, 20) == i
        assert i < 0


def test_limit_neg20_neg400():
    for i in range(-400, -20):
        assert limit(i, 20) == -20
        assert i < 0


def test_limit_cherrypick():
    for i in (20, 40, 60, 100):
        assert limit(i, 20) == 20

    for i in (-20, -40, -60, -100):
        assert limit(i, 20) == -20

    assert limit(-10, 20) == -10
    assert limit(10, 20) == 10


def test_position_difference():
    assert tuple(position_difference((10, 10), (0, 0))) == (10, 10)
    assert tuple(position_difference((10, 10), (-10, -10))) == (20, 20)


def test_position_difference_negative():
    assert tuple(position_difference((-10, -10), (0, 0))) == (-10, -10)
    assert tuple(position_difference((-10, -10), (10, 10))) == (-20, -20)


def test_seconds_function():
    assert seconds(hours=1) == 3600
    assert seconds(minutes=1) == 60
    assert seconds(seconds=10) == 10
    assert seconds(tenths=2) == 0.2

def test_scale_minimap_move_distance():
    assert scale_minimap_move_distance((10, 10)) == (10, 10)
    assert scale_minimap_move_distance((-10, 10)) == (-10, 10)
    assert scale_minimap_move_distance((70, 70)) == (35, 35)
    assert scale_minimap_move_distance((-70, -70)) == (-35, -35)
    assert scale_minimap_move_distance((-70, 70)) == (-35, 35)
    assert scale_minimap_move_distance((70, -70)) == (35, -35)
    assert scale_minimap_move_distance((35, -70)) == (17.5, -35)
