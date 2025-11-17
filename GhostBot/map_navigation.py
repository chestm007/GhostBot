from collections import namedtuple


Zone = namedtuple('Zone', ['location', 'boundary', 'centre', 'scale'])
zones = (
    {
        'simen_mountain': Zone('simen_mountain', ((1270, 1800), (2030, 1280)), (1667, 1544), (-1, 1.2)),
        'barbarian_mountain': Zone('barbarian_mountain', ((1281, 1280), (2050, 510)), (1667, 902), (-1, 1.2)),
        'cloud_mountain': Zone('cloud_mountain', ((-200, 220), (760, -266)), (257, 45), (-1.4, 1.5)),
        'stone_city': Zone('stone_city', ((-70, -266), (490, -760)), (217, -528), (-1, 1.2)),
        'black_wind_camp': Zone('black_wind_camp', ((-762, -270), (-60, -760)), (-415, -497), (-1, 1.1)),
        'laurel_mountain': Zone('laurel_mountain', ((-770, -770), (-260, -1500)), (-489, -1125), (-1.45, 1.65)),
        'snow_mountain': Zone('snow_mountain', ((-1270, -780), (-1075, -1275)), (-1009, -1012), (-0.95, 1.2)),
        'whorl_mountain': Zone('whorl_mountain', ((-1260, -1275), (-800, -2020)), (-1001, -1639), (-1.5, 1.5)),
        'vast_mountain': Zone('vast_mountain', ((491, -280), (1540, -410)), (989, -489), (-1.38, 1.38)),
        'dais_field': Zone('dais_field', ((1540, -20), (3070, -750)), (2304, -453), (-2.05, 2.05))  # FIXME: wrong multiplier
    }
)

_zones_map = {
    'peace_island': ('Moon Dragon Harbor', 'Black Turtle Palace', 'Coconut Woods', 'Peace Village'),
    'simen_mountain': (
        'Bandit Lair',
        'Bandit Fort',
        'East of Simen Mountain',
        'Moon Dragon Village',
        'Outskirt of Village',
        'South of Simen Mountain',
    ),
    'west_simen_mountain': ('Dry Woods', 'Old Site of Village', 'West of Simen Mountain'),
    'cloud_mountain': (
        'Serene Village',
        'Serene Hiking',
        'Cacodaemon Stockade',
        'The Wounded Camp',
        'Bamboo Forest of Cloud Mountain',
        'Centipede Mountain',
    ),
    'stone_city': (
        'Belvedere',
        'Barren Road of West Suburb',
        'Gangster Alley',
        'Green Bamboo Road',
        'Jade Nunnery',
        'Leud Temple',
        'Mushroom Village',
        'Stone City',
        'Stone City North',
        'Stone City South',
    ),
    'black_wind_camp': (
        "Wei's Village",
        'Outside Black Wind Camp',
        'Black Wind Camp',
        'Black Wind Camp Dungeon',
        'West Suburb of Stone City',
        'Arms Bear Residence',
        'Bothy',
    ),
    'laurel_mountain': (
        'Ancient Laurel Grounds',
        'Laurel Road',
        'Laural Room',
        'Red Flower Cave',
        'Fencing Room',
        'Red Flower Alley',
        'Fortune Pond',
        'Fire Cloud Cave',
        'Lava Valley',
        'Laurel Woods',
        'Forest Plain',
        'Spring of Fortune Pond',
        'Fountain Plain',
    ),
    'alchemical_room': (  # laurel mountain mini dungeon
        'Alchemical Room'
    ),
    'snow_mountain': (
        'Snow Forrest',
        'Snow Village',
        'Ghost Shadow Swamp',
        'Ghost Wind Valley',
        'Trade Caravan Camp',
        'White Mountain Shrubberies',
        'White Mountain Cave',
        'Far Temple',
        'Outer Far Temple',
        'Riprap Hillock',
    ),
    'whorl_mountain': (
        'Ice Prick Forest',
        'Live Diagram Zone',
        'Floating Ice Area',
        'Hotspring Valley',
        'Death Diagram Zone',
        'Skull Hollow',
        'Throat Rift Stage',
        'Fiend Hall',
        'Arm Broken Bluff',
    ),
    'vast_mountain': (
        'White Bear Village',
        'Black Bear Cave',
        "Zhao's Palace",
        'Vast Mountain',
        'Wood Demon Cave',
        'Tusk Ogre Lair',
        'Ghost Din Woods',
    ),
    'dais_field': (
        'Yue Mansion',
        'Brier Woods',
        'Avenue',
        'Ling Mansion',
        'Star Town',
        "Chen's Manor",
        "Dai's Field",
        'Ichthyoid Cave',
        'Mazy Woods',
        'Market of Clear Water Dam',
        "New Field of Loo's Village",
        "Old Field of Loo's Village",
        'Jail of Screw Bay',
    ),
}

location_to_zone_map = {sv: k for k, v in _zones_map.items() for sv in v}

def _goto_centre_of_map():
    import logging
    from GhostBot import logger
    from GhostBot.lib.win32.process import PymemProcess
    from GhostBot.bot_controller import ExtendedClient

    logger.setLevel(logging.INFO)
    for proc in PymemProcess.list_clients():
        client = ExtendedClient(proc)
        if client.name == 'iLoveLiIith':
            client.press_key('m')
            client.right_click((int(1024/2), int(768/2)))

if __name__ == '__main__':
    _goto_centre_of_map()
