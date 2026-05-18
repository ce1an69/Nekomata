"""Application configuration loaded from JSON (.neko/settings.json)."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

_SETTINGS_DIR = ".neko"
_SETTINGS_FILE = "settings.json"


@dataclass
class AppConfig:
    api_url: str = ""
    api_key: str | None = None
    model: str = ""

    @classmethod
    def config_exists(cls) -> bool:
        """Check whether a settings file exists (local or user home)."""
        local = Path.cwd() / _SETTINGS_DIR / _SETTINGS_FILE
        user = Path.home() / _SETTINGS_DIR / _SETTINGS_FILE
        return local.exists() or user.exists()

    @classmethod
    def save(cls, api_url: str, api_key: str, model: str) -> AppConfig:
        """Write settings to ./.neko/settings.json and return the new config."""
        path = Path.cwd() / _SETTINGS_DIR / _SETTINGS_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, str] = {"api_url": api_url, "model": model}
        if api_key:
            data["api_key"] = api_key
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        normalized_key = api_key if api_key and api_key.strip() else None
        return cls(api_url=api_url, api_key=normalized_key, model=model)

    @classmethod
    def load(cls) -> AppConfig:
        """Load config from ./.neko/settings.json, falling back to ~/.neko/settings.json."""
        local = Path.cwd() / _SETTINGS_DIR / _SETTINGS_FILE
        user = Path.home() / _SETTINGS_DIR / _SETTINGS_FILE
        for path in (local, user):
            if path.exists():
                return cls._load_from(path)
        return cls()

    @classmethod
    def _load_from(cls, path: Path) -> AppConfig:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Failed to parse %s: %s", path, exc)
            return cls()
        if not isinstance(data, dict):
            log.warning("Unexpected JSON structure in %s", path)
            return cls()

        raw_key = data.get("api_key")
        if raw_key is not None and not raw_key.strip():
            raw_key = None

        return cls(
            api_url=data.get("api_url", ""),
            api_key=raw_key,
            model=data.get("model", ""),
        )
