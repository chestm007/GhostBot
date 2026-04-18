def _format_spot(_spot: str | tuple[int, int]):
    if _spot:
        if isinstance(_spot, str):
            return tuple(_spot.split(" "))
        return f"{' '.join(map(str, _spot))}"
    return ''
