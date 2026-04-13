from GhostBot.lib.var_or_none import var_or_none


def test_var_or_none():
    assert var_or_none('') is None
    assert var_or_none('False', bool) == False