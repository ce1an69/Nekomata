"""Internationalization — loads locale-specific UI strings and spread data."""

import json
import logging

from nekomata._paths import data_dir

log = logging.getLogger(__name__)

LOCALES_DIR = data_dir() / "locales"
SUPPORTED_LANGS = ("en", "zh")
DEFAULT_LANG = "en"
ORNAMENT = "─── ✦ ───"

_current_lang: str = DEFAULT_LANG
_cache: dict[str, dict] = {}


def set_lang(lang: str) -> None:
    if lang not in SUPPORTED_LANGS:
        log.warning(
            "Unsupported language '%s', falling back to '%s'", lang, DEFAULT_LANG
        )
        lang = DEFAULT_LANG
    global _current_lang
    _current_lang = lang


def get_lang() -> str:
    return _current_lang


def _load_locale(name: str) -> dict:
    key = f"{name}:{_current_lang}"
    if key not in _cache:
        path = (
            LOCALES_DIR / f"{_current_lang}.json"
            if name == "ui"
            else LOCALES_DIR / f"{name}_{_current_lang}.json"
        )
        if not path.exists():
            fallback = (
                LOCALES_DIR / f"{name}_{DEFAULT_LANG}.json"
                if name != "ui"
                else LOCALES_DIR / f"{DEFAULT_LANG}.json"
            )
            if fallback.exists():
                path = fallback
            else:
                log.error("Locale file not found: %s", path)
                return {}
        _cache[key] = json.loads(path.read_text(encoding="utf-8"))
    return _cache[key]


def ui_section(name: str) -> dict:
    return _load_locale("ui").get(name, {})


def ui_strings() -> dict:
    return _load_locale("ui")


def spread_strings() -> dict:
    return _load_locale("spreads")


def arcana_label(key: str) -> str:
    return ui_section("arcana_labels").get(key, key)


class _LazySection:
    """Dict proxy that resolves locale strings on each access, not at import time."""

    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        self._name = name

    def __getitem__(self, key: str):
        return ui_section(self._name)[key]

    def get(self, key: str, default=None):
        return ui_section(self._name).get(key, default)


class _LazyStrings:
    """Dict proxy for the full ui strings, resolved on each access."""

    __slots__ = ()

    def __getitem__(self, key: str):
        return ui_strings()[key]

    def get(self, key: str, default=None):
        return ui_strings().get(key, default)


def lazy_section(name: str) -> _LazySection:
    return _LazySection(name)


def lazy_strings() -> _LazyStrings:
    return _LazyStrings()
