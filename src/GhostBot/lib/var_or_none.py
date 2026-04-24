from typing import TypeVar, Union, Optional

_T = TypeVar("_T", bound=Optional[Union[int, str, bool, float, tuple]])

def var_or_none(val: _T, expected_type: type = None) -> _T:
    if val is None:
        return None
    if val == '':
        return None

    if expected_type is not None:
        if expected_type == str:
            return str(val)
        elif expected_type == int:
            return int(val)
        elif expected_type == bool:
            if val in (1, '1', 'True', 'true', True):
                return True
            elif val in (0, '0', 'False', 'false', False):
                return False
            elif val in ('None', 'none'):
                return None
            raise TypeError(f'{val} not a valid {expected_type}')

        elif expected_type == float:
            return float(val)
        elif expected_type == tuple:
            if expected_type == str:
                val = tuple(map(int, val.split(' ')))
            if len(val) == 2:
                return tuple(val)
            return None
        else:
            raise TypeError(f"{type(val)} is not supported by `var_or_none`.")

    if isinstance(val, str):
        return str(val)
    elif isinstance(val, int):
        return int(val)
    elif isinstance(val, bool):
        return bool(val)
    elif isinstance(val, float):
        return float(val)
    elif isinstance(val, tuple):
        if isinstance(val, str):
            val = tuple(map(int, val.split(' ')))
        if len(val) == 2:
            return tuple(val)
        return None
    else:
        raise TypeError(f"{type(val)} is not supported by `var_or_none`.")
