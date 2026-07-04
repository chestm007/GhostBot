"""
Assemble a PORTABLE copy of Tesseract inside the project, at
  src/GhostBot/Tesseract-OCR/
to distribute with the bot -- friends DON'T need to install OCR manually.

Copy only what's needed for runtime OCR (the bot uses --psm 6):
  - tesseract.exe + ALL DLLs (safe; DLLs dominate the size ~70MB,
    the biggest is libicudt (ICU Unicode data), which Tesseract needs).
  - tessdata/eng.traineddata + configs/ + tessconfigs/
Leave OUT (not used at runtime): docs (.html), training tools
(lstmtraining.exe etc.), Java .jar, doc/, and osd.traineddata (~11MB, only
useful for orientation detection -- we don't use it).

The code already looks for this folder first (drop_watcher._find_tesseract).
The folder is GITIGNORED (like the rest of the friends' package) -- recreate with:

    python tools/make_portable_tesseract.py
"""
import os
import shutil
import subprocess

# Source: system installation (same candidates as _find_tesseract).
_SRC_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR",
    r"C:\Program Files (x86)\Tesseract-OCR",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR"),
]
SRC = next((p for p in _SRC_CANDIDATES
            if os.path.exists(os.path.join(p, "tesseract.exe"))), None)

_HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.normpath(os.path.join(_HERE, "..", "src", "GhostBot", "Tesseract-OCR"))


def build() -> None:
    if SRC is None:
        raise SystemExit(
            "Tesseract not found on the system. Install it first "
            "(UB Mannheim: https://github.com/UB-Mannheim/tesseract/wiki)."
        )
    print(f"Source : {SRC}")
    print(f"Dest: {DST}")
    if os.path.exists(DST):
        print("Cleaning old copy...")
        shutil.rmtree(DST)
    os.makedirs(os.path.join(DST, "tessdata"), exist_ok=True)

    # 1) tesseract.exe + all DLLs from root
    n = 0
    for name in os.listdir(SRC):
        low = name.lower()
        if low == "tesseract.exe" or low.endswith(".dll"):
            shutil.copy2(os.path.join(SRC, name), os.path.join(DST, name))
            n += 1
    print(f"  + {n} files (tesseract.exe + DLLs)")

    # 2) tessdata: only English + configs (no osd, no jars, no pdf.ttf)
    td_src = os.path.join(SRC, "tessdata")
    td_dst = os.path.join(DST, "tessdata")
    shutil.copy2(os.path.join(td_src, "eng.traineddata"),
                 os.path.join(td_dst, "eng.traineddata"))
    for sub in ("configs", "tessconfigs"):
        s = os.path.join(td_src, sub)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(td_dst, sub))
    print("  + tessdata/eng.traineddata + configs")


def total_mb(path: str) -> float:
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total / (1024 * 1024)


def verify() -> None:
    """Confirm the copy runs ALONE (without system installation):
    --list-langs only works if tesseract.exe finds the relative tessdata."""
    exe = os.path.join(DST, "tesseract.exe")
    # clean env: remove TESSDATA_PREFIX to force relative search to exe
    env = {k: v for k, v in os.environ.items() if k != "TESSDATA_PREFIX"}
    ver = subprocess.run([exe, "--version"], capture_output=True, text=True, env=env)
    print("  tesseract:", (ver.stdout or ver.stderr).splitlines()[0])
    langs = subprocess.run([exe, "--list-langs"], capture_output=True, text=True, env=env)
    out = (langs.stdout or "") + (langs.stderr or "")
    if "eng" in out:
        print("  OK -- finds tessdata alone (languages: eng)")
    else:
        print("  WARNING -- did not list 'eng'. Output:\n", out)


if __name__ == "__main__":
    build()
    print(f"Done: {DST}  ({total_mb(DST):.0f} MB)")
    verify()
