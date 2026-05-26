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
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from GhostBot import logger

_path_base = os.path.dirname(__file__)


def _webhook_candidates() -> list[str]:
    """Pastas onde discord_webhook.txt pode estar (fonte E .exe compilado)."""
    bases = [
        os.path.join(os.path.expanduser("~"), "GhostBot"),        # config por jogador
        os.path.normpath(os.path.join(_path_base, "..", "..")),   # raiz do repo (fonte)
        _path_base,
    ]
    try:  # pasta do .exe (e /GhostBot) -- onde o pacote dos amigos poe o arquivo
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        bases += [exe_dir, os.path.join(exe_dir, "GhostBot")]
    except Exception:
        pass
    return [os.path.join(b, "discord_webhook.txt") for b in bases]


_WEBHOOK_CANDIDATES = _webhook_candidates()


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


def _post(payload: dict) -> bool:
    """Posta um payload (content e/ou embeds) no webhook. True se enviou OK."""
    url = load_webhook_url()
    if not url:
        logger.warning("discord_notify :: sem URL de webhook (crie discord_webhook.txt)")
        return False
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            # Discord bloqueia o User-Agent padrao do urllib (HTTP 403). Manda um proprio.
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
    except Exception as e:  # rede caiu, URL invalida, etc. -- nao pode derrubar o bot
        logger.error("discord_notify :: falha ao enviar: %s", e)
        return False


def send(content: str, username: str = "Talisman Bot") -> bool:
    """Posta uma mensagem de TEXTO simples no canal via webhook."""
    return _post({"content": content, "username": username})


def send_embed(embed: dict, username: str = "Talisman Bot") -> bool:
    """Posta um EMBED (card bonito) no canal via webhook."""
    return _post({"embeds": [embed], "username": username})


# Cores (decimal) dos cards. Paleta do logo (verde/dourado) + semaforo.
_GOLD = 0xFCB400    # drop alvo
_GRAY = 0x95A5A6    # item novo (a decidir)
_RED = 0xE03131     # morte
_ORANGE = 0xE67E22  # mochila cheia


def _embed(title: str, description: str, color: int, char: str | None = None) -> dict:
    """Monta um embed padrao: titulo + descricao + cor + char no rodape + horario."""
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
    """Alerta de drop como embed, conforme a categoria (want / unknown).

    `color`: override opcional da cor do card. Quando a deteccao de RARIDADE
    (pela cor do nome no jogo) ficar pronta, e so passar a cor da raridade aqui
    -- o resto do card ja esta montado."""
    if category == "want":
        embed = _embed("🎯 Drop alvo!", f"**{item}**", color or _GOLD, char)
    else:  # unknown / item novo
        embed = _embed(
            "❓ Item novo",
            f"**{item}**\n_Decida em qual lista colocar (✅ Quero / ❌ Não quero no app)._",
            color or _GRAY, char,
        )
    return send_embed(embed)


def send_death_alert(char: str | None = None) -> bool:
    """Avisa no Discord que o personagem morreu (HP chegou a 0)."""
    return send_embed(_embed("💀 Morte!", "O personagem morreu.", _RED, char))


def send_inventory_full_alert(char: str | None = None) -> bool:
    """Avisa no Discord que a mochila encheu ('Your item box is full.')."""
    return send_embed(_embed("📦 Mochila cheia!", "Indo vender.", _ORANGE, char))
