"""
Captura icone de item do TO via clipboard e salva como BMP.

Fluxo:
  1. Roda o script.
  2. Escolhe a categoria (SELL, DELETE, ALERTS/RARE, etc.).
  3. Digita o nome do item (sem espacos, ex: 'DragonRing').
  4. No jogo: aperta Win+Shift+S, recorta o icone do item.
  5. Volta no terminal e aperta Enter -- o script le da area de transferencia
     e salva como Images/<categoria>/<nome>.bmp.
  6. Pergunta se quer capturar outro.

Requer: Pillow (ja esta em pyproject.toml).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from PIL import ImageGrab, Image


# pasta root das imagens do bot
IMAGES_ROOT = Path(__file__).resolve().parent.parent / "src" / "GhostBot" / "Images"

# categorias pre-existentes + sugestoes novas
CATEGORIES = {
    "1": ("SELL", "Itens que o NPC compra (auto-sell)"),
    "2": ("DELETE", "Itens pra apagar (limpa bag)"),
    "3": ("BC_DELETE", "Delete especifico Bird's Cave"),
    "4": ("ALERTS/BLUE", "Alerta Discord -- raridade azul"),
    "5": ("ALERTS/PURPLE", "Alerta Discord -- raridade roxa"),
    "6": ("ALERTS/BOSS", "Alerta Discord -- drop de Boss"),
    "7": ("misc", "Elementos de UI (botoes, dialogs do jogo)"),
    "8": ("custom", "Outra pasta (voce digita)"),
}


def menu_pick_category() -> Path:
    print("\nCategoria:")
    for k, (folder, desc) in CATEGORIES.items():
        existing = IMAGES_ROOT / folder
        count = ""
        if existing.is_dir():
            n = len([f for f in existing.iterdir() if f.suffix.lower() == ".bmp"])
            count = f"  [{n} bmps]"
        print(f"  {k}. {folder}{count}  -- {desc}")

    while True:
        choice = input("> ").strip()
        if choice in CATEGORIES:
            folder, _ = CATEGORIES[choice]
            if folder == "custom":
                folder = input("Pasta dentro de Images/ (ex: ALERTS/LEGENDARY): ").strip().strip("/\\")
            target = IMAGES_ROOT / folder
            target.mkdir(parents=True, exist_ok=True)
            return target
        print("Opcao invalida. Escolhe um numero da lista.")


def ask_item_name(target: Path) -> str | None:
    while True:
        name = input("Nome do item (sem .bmp, sem espacos -- vazio pra cancelar): ").strip()
        if not name:
            return None
        if "/" in name or "\\" in name or name.startswith("."):
            print("  Nome invalido. Sem barras nem pontos no inicio.")
            continue
        bmp_path = target / f"{name}.bmp"
        if bmp_path.exists():
            ans = input(f"  '{bmp_path.name}' ja existe. Sobrescrever? [s/N] ").strip().lower()
            if ans != "s":
                continue
        return name


def grab_clipboard_image() -> Image.Image | None:
    img = ImageGrab.grabclipboard()
    if img is None:
        return None
    if isinstance(img, list):
        # clipboard tem caminho de arquivo, nao imagem
        return None
    return img


def capture_one():
    target = menu_pick_category()
    print(f"\nPasta destino: {target}")

    name = ask_item_name(target)
    if name is None:
        return False

    print(
        "\n>>> Agora no jogo: aperta Win+Shift+S, recorta SO o icone do item\n"
        "    (apertado bem nas bordas), depois aperta ENTER aqui.\n"
    )
    input("Pressione ENTER quando tiver recortado: ")

    img = grab_clipboard_image()
    if img is None:
        print("  ERRO: area de transferencia nao tem imagem.")
        print("  Voce recortou com Win+Shift+S? Tenta de novo.")
        return True  # loop continua

    # converte pra RGB e salva como BMP (mesmo formato dos arquivos atuais)
    img_rgb = img.convert("RGB")
    bmp_path = target / f"{name}.bmp"
    img_rgb.save(bmp_path, format="BMP")

    size_kb = bmp_path.stat().st_size / 1024
    print(f"\n  OK -- salvo: {bmp_path.relative_to(IMAGES_ROOT.parent.parent.parent)}")
    print(f"         tamanho: {img.width}x{img.height}  ({size_kb:.1f} KB)\n")
    return True


def main():
    if not IMAGES_ROOT.is_dir():
        print(f"ERRO: pasta de imagens nao encontrada em {IMAGES_ROOT}")
        sys.exit(1)

    print("=" * 60)
    print("  Captura de icone de item -- BotTO")
    print("=" * 60)
    print(f"  Pasta base: {IMAGES_ROOT}")

    while True:
        if not capture_one():
            break
        again = input("Capturar outro? [S/n] ").strip().lower()
        if again == "n":
            break

    print("\nFim. Os BMPs salvos vao ser carregados na proxima vez que o bot rodar.")


if __name__ == "__main__":
    main()
