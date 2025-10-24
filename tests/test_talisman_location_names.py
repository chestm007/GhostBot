from GhostBot.lib.talisman_location_names import location_to_name


def test_location_to_name():
    assert location_to_name((285, -509)) == "Stone City"
    assert location_to_name((895, -500)) == "Vast Mountain"
    assert location_to_name((2594, -316)) == "Dai's Field"