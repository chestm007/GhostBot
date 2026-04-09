from typing import TypeVar, Union, Optional

_T = TypeVar("_T", bound=Optional[Union[int, str, bool, float, tuple]])

def var_or_none(val: _T) -> _T:
    if val is None:
        return None

    _func = None
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
