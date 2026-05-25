"""
Envio de alertas pro Discord via WEBHOOK (so ENVIA, nao e bot interativo).

A URL do webhook e SECRETA e fica num arquivo LOCAL `discord_webhook.txt`,
FORA do git (.gitignore). NUNCA hardcodar a URL aqui no codigo.

Procura o arquivo (nesta ordem):
  1. ~/GhostBot/discord_webhook.txt   (config por jogador, igual aos .yml)
  2. raiz do repo / pasta do .exe
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from GhostBot import logger

_path_base = os.path.dirname(__file__)

_WEBHOOK_CANDIDATES = [
    os.path.join(os.path.expanduser("~"), "GhostBot", "discord_webhook.txt"),
    os.path.normpath(os.path.join(_path_base, "..", "..", "discord_webhook.txt")),
    os.path.join(_path_base, "discord_webhook.txt"),
]


def load_webhook_url() -> str | None:
    """Primeira linha que comeca com https:// no arquivo de webhook (ignora # e vazias)."""
    for path in _WEBHOOK_CANDIDATES:
        try:
            for raw in Path(path).read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if line.lower().startswith("https://"):
                    return line
        except (FileNotFoundError, OSError):
            continue
    return None


def send(content: str, username: str = "Talisman Bot") -> bool:
    """Posta uma mensagem simples no canal via webhook. True se enviou OK."""
    url = load_webhook_url()
    if not url:
        logger.warning("discord_notify :: sem URL de webhook (crie discord_webhook.txt)")
        return False
    payload = json.dumps({"content": content, "username": username}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            # Discord bloqueia o User-Agent padrao do urllib (HTTP 403). Manda um proprio.
            "User-Agent": "TalismanBot/1.0 (+https://github.com/chestm007/GhostBot)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 204):
                return True
            logger.warning("discord_notify :: status inesperado %s", resp.status)
            return False
    except Exception as e:  # rede caiu, URL invalida, etc. -- nao pode derrubar o bot
        logger.error("discord_notify :: falha ao enviar: %s", e)
        return False


def send_drop_alert(item: str, category: str, char: str | None = None) -> bool:
    """Monta e envia o alerta de drop conforme a categoria (want / unknown)."""
    who = f" — **{char}**" if char else ""
    if category == "want":
        msg = f"🎯 **DROP ALVO:** {item}{who}"
    else:  # unknown / item novo
        msg = f"❓ Item novo: **{item}**{who}  _(decida em qual lista colocar)_"
    return send(msg)


def send_death_alert(char: str | None = None) -> bool:
    """Avisa no Discord que o personagem morreu (HP chegou a 0)."""
    who = f" — **{char}**" if char else ""
    return send(f"💀 **MORTE!** O personagem morreu{who}")
