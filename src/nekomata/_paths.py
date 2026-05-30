"""Centralized path resolution for dev, pip-installed, and PyInstaller frozen mode."""

import sys
from pathlib import Path


def base_dir() -> Path:
    """Package directory (src/nekomata/) in dev/pip mode, or sys._MEIPASS when frozen."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    return base_dir() / "data"


def assets_dir() -> Path:
    return base_dir() / "assets"


def static_dir() -> Path:
    # In frozen mode, nekomata.spec remaps web/static → static at the bundle root.
    # In dev/pip mode, static lives at <package>/web/static/.
    if getattr(sys, "frozen", False):
        return base_dir() / "static"
    return base_dir() / "web" / "static"
