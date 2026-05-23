#!/usr/bin/env python3
"""Cross-platform build script for Nekomata desktop app.

Usage:
    python scripts/build_desktop.py          # build with PyInstaller
    python scripts/build_desktop.py --clean   # clean previous build first
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "nekomata.spec"


def main():
    if "--clean" in sys.argv:
        for d in (ROOT / "build", ROOT / "dist"):
            if d.exists():
                print(f"Removing {d}")
                shutil.rmtree(d)

    subprocess.check_call(
        [sys.executable, "-m", "PyInstaller", str(SPEC), "--noconfirm"],
        cwd=ROOT,
    )

    if sys.platform == "darwin":
        app = ROOT / "dist" / "Nekomata.app"
        if app.exists():
            size = sum(f.stat().st_size for f in app.rglob("*") if f.is_file())
            print(f"\nBuilt: {app} ({size / 1024 / 1024:.1f} MB)")
    else:
        dist = ROOT / "dist" / "Nekomata"
        if dist.exists():
            size = sum(f.stat().st_size for f in dist.rglob("*") if f.is_file())
            print(f"\nBuilt: {dist} ({size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
