"""
Monta uma copia PORTATIL do Tesseract dentro do projeto, em
  src/GhostBot/Tesseract-OCR/
pra distribuir junto com o bot -- os amigos NAO precisam instalar OCR na mao.

Copia so o necessario pro OCR em runtime (o bot usa --psm 6):
  - tesseract.exe + TODAS as DLLs (seguro; as DLLs dominam o tamanho ~70MB,
    a maior e a libicudt (dados Unicode do ICU), que o Tesseract precisa).
  - tessdata/eng.traineddata + configs/ + tessconfigs/
Deixa de FORA (nao usado em runtime): docs (.html), ferramentas de treino
(lstmtraining.exe etc.), .jar do Java, doc/, e o osd.traineddata (~11MB, so
serve pra deteccao de orientacao -- nao usamos).

O codigo ja procura essa pasta primeiro (drop_watcher._find_tesseract).
A pasta e GITIGNORADA (igual ao resto do pacote dos amigos) -- recrie com:

    python tools/make_portable_tesseract.py
"""
import os
import shutil
import subprocess

# Origem: instalacao do sistema (mesmos candidatos do _find_tesseract).
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
            "Tesseract nao encontrado no sistema. Instale primeiro "
            "(UB Mannheim: https://github.com/UB-Mannheim/tesseract/wiki)."
        )
    print(f"Origem : {SRC}")
    print(f"Destino: {DST}")
    if os.path.exists(DST):
        print("Limpando copia antiga...")
        shutil.rmtree(DST)
    os.makedirs(os.path.join(DST, "tessdata"), exist_ok=True)

    # 1) tesseract.exe + todas as DLLs da raiz
    n = 0
    for name in os.listdir(SRC):
        low = name.lower()
        if low == "tesseract.exe" or low.endswith(".dll"):
            shutil.copy2(os.path.join(SRC, name), os.path.join(DST, name))
            n += 1
    print(f"  + {n} arquivos (tesseract.exe + DLLs)")

    # 2) tessdata: so o ingles + os configs (sem osd, sem jars, sem pdf.ttf)
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
    """Confirma que a copia roda SOZINHA (sem a instalacao do sistema):
    --list-langs so funciona se o tesseract.exe achar o tessdata relativo."""
    exe = os.path.join(DST, "tesseract.exe")
    # ambiente limpo: tira TESSDATA_PREFIX pra forcar a busca relativa ao exe
    env = {k: v for k, v in os.environ.items() if k != "TESSDATA_PREFIX"}
    ver = subprocess.run([exe, "--version"], capture_output=True, text=True, env=env)
    print("  tesseract:", (ver.stdout or ver.stderr).splitlines()[0])
    langs = subprocess.run([exe, "--list-langs"], capture_output=True, text=True, env=env)
    out = (langs.stdout or "") + (langs.stderr or "")
    if "eng" in out:
        print("  OK -- acha o tessdata sozinho (idiomas: eng)")
    else:
        print("  ATENCAO -- nao listou 'eng'. Saida:\n", out)


if __name__ == "__main__":
    build()
    print(f"Pronto: {DST}  ({total_mb(DST):.0f} MB)")
    verify()
