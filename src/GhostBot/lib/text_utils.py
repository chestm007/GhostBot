from __future__ import annotations

import re

_LVL_RE = re.compile(r"\s*\(lvl\s*\d+\)\s*$", re.IGNORECASE)


def clean_item_name(raw: str) -> str:
    return _LVL_RE.sub("", raw).strip()
