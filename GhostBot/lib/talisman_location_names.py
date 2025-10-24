def location_to_name(location: tuple[int, int]) -> str | None:
    x, y = location
    if 70 < x < 500 and -250 > y > -780:
        return "Stone City"
    if 500 < x < 1520 and -270 > y > -770:
        return "Vast Mountain"
    if 1520 < x < 3100 and 0 > y > -770:
        return "Dai's Field"
    return None