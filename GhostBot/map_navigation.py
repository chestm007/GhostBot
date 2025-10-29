from collections import namedtuple

Zone = namedtuple('Zone', ['location', 'boundary', 'centre', 'scale'])
zones = (
    {
        'simen_mountain': Zone('simen_mountain', ((1270, 1800), (2030, 1280)), (1667, 1544), (-1, 1.2)),
        'barbarian_mountain': Zone('barbarian_mountain', ((1281, 1280), (2050, 510)), (1667, 902), (-1, 1.2)),
    }
)

_zones_map = {
    'peace_island': ('Moon Dragon Harbor', 'Black Turtle Palace', 'Coconut Woods', 'Peace Village'),
    'simen_mountain': (
        'Bandit Lair',
        'East of Simen Mountain',
        'Moon Dragon Village',
        'Outskirt of Village',
        'South of Simen Mountain',
    ),
    'west_simen_mountain': ('Dry Woods', 'Old Site of Village', 'West of Simen Mountain'),
}

location_to_zone_map = {sv: k for k, v in _zones_map.items() for sv in v}