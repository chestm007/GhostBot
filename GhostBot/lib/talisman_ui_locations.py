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
    surroundings_firstitem=(290, 262),
    view_reset=(867, 57),
    stall=(920, 190),
    #sell_item_button=(275, 430),
    sell_item_button=(275, 400),
    #npc_location=(490, 400),
    npc_location=(500, 405),
    sell_item_slot_1=(455, 270),
    confirm_sell_button=(475, 713),
)

TeamLocations = [UI_locations.player, UI_locations.team_1, UI_locations.team_2, UI_locations.team_3, UI_locations.team_4]