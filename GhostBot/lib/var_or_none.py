def _str(val):
    return str(val) if val else None

def _int(val):
    return int(val) if val else None

def _bool(val):
    return bool(val) if val else None

def _float(val):
    return float(val) if val else None

def _eval(val):
    return eval(val) if val else None

def _tuple(val):
    if not val:
        return None
    if isinstance(val, str):
        val = tuple(map(int, val.split(' ')))
    if len(val) == 2:
        return tuple(val)
    print(val, type(val))
    return None