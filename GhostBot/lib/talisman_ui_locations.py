from attrdict import AttrDict

UI_locations = AttrDict(
        player=(40, 40),
        team_1=(30, 200),
        team_2=(30, 285),
        team_3=(30, 365),
        team_4=(30, 445),
        minimap_centre=(919, 115),
        minimap_surroundings=(975, 60),
        surroundings_search=(570, 540),
        surroundings_firstitem=(290, 262)
)

TeamLocations = [UI_locations.player, UI_locations.team_1, UI_locations.team_2, UI_locations.team_3, UI_locations.team_4]