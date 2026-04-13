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
            if isinstance(val, int):
                if val == 1:
                    return True
                elif val == 0:
                    return False
                raise TypeError(f'{val} not a valid {expected_type}')

            if isinstance(val, str):
                if val.lower() == 'true':
                    return True
                elif val.lower() == 'false':
                    return False
                elif val.lower() == 'none':
                    return None
                raise TypeError(f'{val} not a valid {expected_type}')

            return bool(val)

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
