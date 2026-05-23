"""Centralized UI string loading — parses data/ui_strings.json once."""

import json

from nekomata._paths import data_dir

DATA_DIR = data_dir()
_STRINGS: dict | None = None
ORNAMENT = "─── ✦ ───"


def _load() -> dict:
    global _STRINGS
    if _STRINGS is None:
        _STRINGS = json.loads(
            (DATA_DIR / "ui_strings.json").read_text(encoding="utf-8")
        )
    return _STRINGS


def section(name: str) -> dict:
    """Return a top-level section from ui_strings.json."""
    return _load()[name]


def all_strings() -> dict:
    """Return the entire ui_strings.json dict."""
    return _load()
