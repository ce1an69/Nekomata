#!/usr/bin/env python3
"""Cross-platform build script for Nekomata desktop app.

Usage:
    python scripts/build_desktop.py          # build with PyInstaller
    python scripts/build_desktop.py --clean   # clean previous build first
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "nekomata.spec"


def create_dmg(app_path: Path) -> None:
    """Create a macOS DMG with drag-to-Applications layout."""
    dmg_path = ROOT / "dist" / "Nekomata.dmg"

    with tempfile.TemporaryDirectory(prefix="nekomata-dmg-") as tmp:
        staging = Path(tmp)
        shutil.copytree(app_path, staging / app_path.name)
        (staging / "Applications").symlink_to("/Applications")

        if dmg_path.exists():
            dmg_path.unlink()

        subprocess.check_call([
            "hdiutil", "create",
            "-volname", "Nekomata",
            "-srcfolder", str(staging),
            "-ov",
            "-format", "UDZO",
            str(dmg_path),
        ])

    size_mb = dmg_path.stat().st_size / 1024 / 1024
    print(f"DMG:  {dmg_path} ({size_mb:.1f} MB)")


def main():
    if sys.platform == "win32" and sys.version_info >= (3, 14):
        raise SystemExit(
            "Windows desktop build requires Python 3.13 because pywebview's "
            "WinForms backend depends on pythonnet, which does not support "
            "Python 3.14 yet. Use .venv-win\\Scripts\\python.exe."
        )

    if "--clean" in sys.argv:
        for d in (ROOT / "build", ROOT / "dist"):
            if d.exists():
                print(f"Removing {d}")
                shutil.rmtree(d)

    subprocess.check_call(
        [sys.executable, "-m", "PyInstaller", str(SPEC), "--noconfirm"],
        cwd=ROOT,
    )

    if sys.platform == "win32":
        exe = ROOT / "dist" / "Nekomata.exe"
        if exe.exists():
            print(f"\nBuilt: {exe} ({exe.stat().st_size / 1024 / 1024:.1f} MB)")
    elif sys.platform == "darwin":
        app = ROOT / "dist" / "Nekomata.app"
        if app.exists():
            size = sum(f.stat().st_size for f in app.rglob("*") if f.is_file())
            print(f"\nApp:  {app} ({size / 1024 / 1024:.1f} MB)")
            create_dmg(app)
    else:
        dist = ROOT / "dist" / "Nekomata"
        if dist.exists():
            size = sum(f.stat().st_size for f in dist.rglob("*") if f.is_file())
            print(f"\nBuilt: {dist} ({size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
