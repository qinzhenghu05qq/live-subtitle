"""打包前一次性预下载：Vosk 英文小模型 + Argos en->zh 翻译模型。

下载完后这两份资源进入 models/ 和 argos-packages/，PyInstaller 会把它们打入安装包。
"""
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path
# Windows 默认 cp1252 控制台不能打印 Unicode（如 argos pkg 的 __repr__ 里含 →）
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VOSK_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
ARGOS_PKG_DIR = ROOT / "argos-packages"


def _hook(blocks: int, block_size: int, total: int) -> None:
    done = blocks * block_size
    if total > 0:
        sys.stdout.write(f"\r  {done / 1024 / 1024:.1f} / {total / 1024 / 1024:.1f} MB")
    else:
        sys.stdout.write(f"\r  {done / 1024 / 1024:.1f} MB")
    sys.stdout.flush()


def download(url: str, dest: Path) -> None:
    print(f"Downloading {url}\n  -> {dest}")
    urllib.request.urlretrieve(url, dest, _hook)
    print()


def fetch_vosk() -> None:
    target = MODELS / "vosk-en"
    if target.exists() and any(target.iterdir()):
        print("[skip] vosk-en already present")
        return
    MODELS.mkdir(exist_ok=True)
    zp = MODELS / "vosk-en.zip"
    download(VOSK_URL, zp)
    print("Extracting...")
    with zipfile.ZipFile(zp) as z:
        z.extractall(MODELS)
    for n in os.listdir(MODELS):
        p = MODELS / n
        if p.is_dir() and n.startswith("vosk-model"):
            if target.exists():
                shutil.rmtree(target)
            p.rename(target)
            break
    zp.unlink(missing_ok=True)
    print(f"[ok] vosk-en at {target}")


def fetch_argos() -> None:
    ARGOS_PKG_DIR.mkdir(exist_ok=True)
    target = ARGOS_PKG_DIR / "translate-en_zh.argosmodel"
    if target.exists():
        print("[skip] argos en->zh already present")
        return
    import argostranslate.package
    print("Updating argos package index...")
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    pkg = next(
        (p for p in available if p.from_code == "en" and p.to_code == "zh"),
        None,
    )
    if pkg is None:
        raise RuntimeError("No en->zh package available in argos index")
    print(f"Downloading argos package {pkg.from_code} -> {pkg.to_code} (v{getattr(pkg, 'package_version', '?')}) ...")
    src_path = pkg.download()
    shutil.copy(src_path, target)
    print(f"[ok] argos en->zh at {target}")


def main() -> None:
    fetch_vosk()
    fetch_argos()
    print("\nAll assets ready.")


if __name__ == "__main__":
    main()
