"""Centralized path resolution for dev and PyInstaller frozen mode."""

import sys
from pathlib import Path


def base_dir() -> Path:
    """Project root in dev mode, or sys._MEIPASS when frozen."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    # _paths.py is at src/nekomata/_paths.py → parents[2] = project root
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return base_dir() / "data"


def assets_dir() -> Path:
    return base_dir() / "assets"


def static_dir() -> Path:
    if getattr(sys, "frozen", False):
        return base_dir() / "static"
    return Path(__file__).resolve().parent / "web" / "static"
