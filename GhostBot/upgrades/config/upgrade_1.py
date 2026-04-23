from traceback import print_exception
from typing import Any


def main(config_yaml: dict[str, Any]):
    """refactors regen.spot and sell.return_spot to attack.spot"""

    _attack_spot, _regen_spot, _sell_spot = None, None, None

    if _attack_config := config_yaml.get('attack'):
        _attack_spot = _attack_config.get("spot")

    if _regen_config := config_yaml.get("regen"):
        _regen_spot = _regen_config.get("spot")

    if _sell_config := config_yaml.get("sell"):
        _sell_spot = _sell_config.get("return_spot")

    if _attack_spot and not (_sell_spot or _regen_spot):
        return config_yaml

    if _regen_spot:
        if not _attack_spot:
            if config_yaml.get('attack'):
                config_yaml['attack']['spot'] = _regen_spot
            elif config_yaml.get('fairy'):
                config_yaml['fairy']['spot'] = _regen_spot
            _attack_spot = _regen_spot
        try:
            del config_yaml['regen']['spot']
        except Exception as e:
            print_exception(e)
            pass
    if _sell_spot:
        if not _attack_spot:
            if config_yaml.get('attack'):
                config_yaml['attack']['spot'] = _sell_spot
            elif config_yaml.get('fairy'):
                config_yaml['fairy']['spot'] = _sell_spot
        try:
            del config_yaml['sell']['return_spot']
        except Exception as e:
            print_exception(e)
            pass
    return config_yaml
