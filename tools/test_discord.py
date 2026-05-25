"""
Teste do webhook do Discord: manda uma mensagem de teste no canal.

Antes de rodar, cole a URL do webhook em discord_webhook.txt (raiz do projeto).

Uso:
    python tools/test_discord.py
"""
import sys

sys.path.insert(0, r"C:\Bot\BotTO\src")

from GhostBot.discord_notify import load_webhook_url, send

url = load_webhook_url()
if not url:
    raise SystemExit(
        "Nenhuma URL encontrada. Cole a URL do webhook em discord_webhook.txt "
        "(uma linha comecando com https://)."
    )

# mostra so o comecinho, pra confirmar que carregou sem vazar a chave inteira
print(f"URL carregada: {url[:45]}...")
ok = send("✅ Teste do **Talisman Bot** — webhook conectado com sucesso!")
print("ENVIADO! Confere o canal do Discord." if ok else "FALHOU. Ver o log de erro acima.")
