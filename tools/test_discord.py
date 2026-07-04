"""
Discord webhook test: send a test message to the channel.

Before running, paste the webhook URL in discord_webhook.txt (project root).

Usage:
    python tools/test_discord.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from GhostBot.discord_notify import (
    load_webhook_url, send,
    send_drop_alert, send_death_alert, send_inventory_full_alert,
)

url = load_webhook_url()
if not url:
    raise SystemExit(
         "No URL found. Paste the webhook URL in discord_webhook.txt "
         "(one line starting with https://)."
    )

# show only the beginning, to confirm it loaded without leaking the full key
print(f"URL carregada: {url[:45]}...")
ok = send("✅ Teste do **Talisman Bot** — webhook conectado com sucesso!")
print("SENT! Check the Discord channel." if ok else "FAILED. See error log above.")

# Preview of the 4 new CARDS (embeds) -- to see how they look in the channel.
print("Mandando previa dos cards (embeds)...")
char = "teste123"
send_drop_alert("Large Ruby", "want", char)        # 🎯 dourado
send_drop_alert("Animal Fur", "unknown", char)     # ❓ cinza
send_inventory_full_alert(char)                    # 📦 laranja
send_death_alert(char)                             # 💀 vermelho
print("Preview sent. Check the 4 cards in the Discord channel.")
