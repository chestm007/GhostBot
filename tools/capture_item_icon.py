"""
Capture TO item icon via clipboard and save as BMP.

Flow:
  1. Run the script.
  2. Choose the category (SELL, DELETE, ALERTS/RARE, etc.).
  3. Type the item name (no spaces, e.g. 'DragonRing').
  4. In-game: press Win+Shift+S, crop the item icon.
  5. Back in terminal and press Enter -- the script reads from clipboard
     and saves as Images/<category>/<name>.bmp.
  6. Asks if you want to capture another.

Requires: Pillow (already in pyproject.toml).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from PIL import ImageGrab, Image


# root image folder for the bot
IMAGES_ROOT = Path(__file__).resolve().parent.parent / "src" / "GhostBot" / "Images"

# categorias pre-existentes + sugestoes novas
CATEGORIES = {
    "1": ("SELL", "Items the NPC buys (auto-sell)"),
    "2": ("DELETE", "Items to delete (clear bag)"),
    "3": ("BC_DELETE", "Specific Bird's Cave delete"),
    "4": ("ALERTS/BLUE", "Discord alert -- blue rarity"),
    "5": ("ALERTS/PURPLE", "Discord alert -- purple rarity"),
    "6": ("ALERTS/BOSS", "Discord alert -- Boss drop"),
    "7": ("misc", "UI elements (buttons, game dialogs)"),
    "8": ("custom", "Other folder (you type it)"),
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
        print("Invalid option. Pick a number from the list.")


def ask_item_name(target: Path) -> str | None:
    while True:
        name = input("Item name (no .bmp, no spaces -- empty to cancel): ").strip()
        if not name:
            return None
        if "/" in name or "\\" in name or name.startswith("."):
            print("  Invalid name. No slashes or dots at the start.")
            continue
        bmp_path = target / f"{name}.bmp"
        if bmp_path.exists():
            ans = input(f"  '{bmp_path.name}' already exists. Overwrite? [s/N] ").strip().lower()
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
        "\n>>> Now in-game: press Win+Shift+S, crop ONLY the item icon\n"
        "    (snug on the edges), then press ENTER here.\n"
    )
    input("Press ENTER when you've cropped: ")

    img = grab_clipboard_image()
    if img is None:
        print("  ERROR: clipboard has no image.")
        print("  Did you crop with Win+Shift+S? Try again.")
        return True  # loop continues

    # convert to RGB and save as BMP (same format as current files)
    img_rgb = img.convert("RGB")
    bmp_path = target / f"{name}.bmp"
    img_rgb.save(bmp_path, format="BMP")

    size_kb = bmp_path.stat().st_size / 1024
    print(f"\n  OK -- salvo: {bmp_path.relative_to(IMAGES_ROOT.parent.parent.parent)}")
    print(f"         tamanho: {img.width}x{img.height}  ({size_kb:.1f} KB)\n")
    return True


def main():
    if not IMAGES_ROOT.is_dir():
        print(f"ERROR: image folder not found at {IMAGES_ROOT}")
        sys.exit(1)

    print("=" * 60)
    print("  Captura de icone de item -- BotTO")
    print("=" * 60)
    print(f"  Pasta base: {IMAGES_ROOT}")

    while True:
        if not capture_one():
            break
        again = input("Capture another? [S/n] ").strip().lower()
        if again == "n":
            break

    print("\nDone. The saved BMPs will be loaded next time the bot runs.")


if __name__ == "__main__":
    main()
