"""
Send alerts to Discord via WEBHOOK (SEND only, not an interactive bot).

The webhook URL is SECRET and lives in a local `discord_webhook.txt` file,
OUTSIDE git (.gitignore). NEVER hardcode the URL in code.

Search for the file (in this order):
  1. ~/GhostBot/discord_webhook.txt   (per-player config, same as .yml)
  2. repo root / .exe folder
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from GhostBot import logger

_path_base = os.path.dirname(__file__)


def _webhook_candidates() -> list[str]:
    """Folders where discord_webhook.txt may be (source AND compiled .exe)."""
    bases = [
        os.path.join(os.path.expanduser("~"), "GhostBot"),        # config por jogador
        os.path.normpath(os.path.join(_path_base, "..", "..")),   # raiz do repo (fonte)
        _path_base,
    ]
    try:  # .exe folder (and /GhostBot) -- where the friends' package puts the file
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        bases += [exe_dir, os.path.join(exe_dir, "GhostBot")]
    except Exception:
        pass
    return [os.path.join(b, "discord_webhook.txt") for b in bases]


_WEBHOOK_CANDIDATES = _webhook_candidates()


def load_webhook_url() -> str | None:
    """First line starting with https:// in the webhook file (ignores # and empty lines)."""
    for path in _WEBHOOK_CANDIDATES:
        try:
            for raw in Path(path).read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if line.lower().startswith("https://"):
                    return line
        except (FileNotFoundError, OSError):
            continue
    return None


def _post(payload: dict) -> bool:
    """Post a payload (content and/or embeds) to the webhook. True if sent OK."""
    url = load_webhook_url()
    if not url:
        logger.warning("discord_notify :: no webhook URL (create discord_webhook.txt)")
        return False
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            # Discord blocks urllib's default User-Agent (HTTP 403). Send our own.
            "User-Agent": "TalismanBot/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 204):
                return True
            logger.warning("discord_notify :: status inesperado %s", resp.status)
            return False
    except Exception as e:  # network down, invalid URL, etc. -- don't crash the bot
        logger.error("discord_notify :: falha ao enviar: %s", e)
        return False


def send(content: str, username: str = "Talisman Bot") -> bool:
    """Post a plain TEXT message to the channel via webhook."""
    return _post({"content": content, "username": username})


def send_embed(embed: dict, username: str = "Talisman Bot") -> bool:
    """Post an EMBED (pretty card) to the channel via webhook."""
    return _post({"embeds": [embed], "username": username})


# Card colors (decimal). Logo palette (green/gold) + traffic light.
_GOLD = 0xFCB400    # target drop
_GRAY = 0x95A5A6    # new item (to be decided)
_RED = 0xE03131     # death
_ORANGE = 0xE67E22  # inventory full


def _embed(title: str, description: str, color: int, char: str | None = None) -> dict:
    """Build a standard embed: title + description + color + char footer + timestamp."""
    e = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if char:
        e["footer"] = {"text": f"👤 {char}"}
    return e


def send_drop_alert(item: str, category: str, char: str | None = None,
                    color: int | None = None) -> bool:
    """Drop alert as embed, per category (want / unknown).

    `color`: optional override of the card color. When RARITY detection
    (by item name color in-game) is ready, just pass the rarity color here
    -- the rest of the card is already built."""
    if category == "want":
        embed = _embed("🎯 Target drop!", f"**{item}**", color or _GOLD, char)
    else:  # unknown / new item
        embed = _embed(
            "❓ New item",
            f"**{item}**\n_Decide which list to put it in (✅ Want / ❌ Don't want in the app)._",
            color or _GRAY, char,
        )
    return send_embed(embed)


def send_death_alert(char: str | None = None) -> bool:
    """Alert on Discord that the character died (HP reached 0)."""
    return send_embed(_embed("💀 Death!", "The character died.", _RED, char))


def send_inventory_full_alert(char: str | None = None) -> bool:
    """Alert on Discord that the inventory is full ('Your item box is full.')."""
    return send_embed(_embed("📦 Inventory full!", "Going to sell.", _ORANGE, char))
