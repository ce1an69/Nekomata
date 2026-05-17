"""Application configuration loaded from TOML (config.toml)."""


import logging
import tomllib
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class AppConfig:
    ai_backend: str = "template"
    ai_model: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str | None = None
    ai_timeout: float = 60.0
    ai_style: str = "mystical"
    ai_fallback: bool = True
    display_animation: bool = True
    display_theme: str = "catppuccin"
    reversal_prob: float = 0.5

    # Project root directory (where config.toml and assets/ live)
    _PROJECT_ROOT = Path(__file__).resolve().parents[3]

    @classmethod
    def load(cls, path: Path | None = None) -> AppConfig:
        """Load config from a TOML file, falling back to defaults for missing keys."""
        defaults = cls()
        if path is None:
            path = cls._PROJECT_ROOT / "config.toml"
        if not path.exists():
            return defaults
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError:
            log.warning("Failed to parse %s, using defaults", path)
            return defaults

        ai = data.get("ai", {})
        display = data.get("display", {})
        reversal = data.get("reversal", {})

        raw_key = ai.get("api_key", defaults.ai_api_key)
        # Normalize empty-string API keys to None so the interpreter skips the header
        if raw_key is not None and not raw_key.strip():
            raw_key = None

        return cls(
            ai_backend=ai.get("backend", defaults.ai_backend),
            ai_model=ai.get("model", defaults.ai_model),
            ai_base_url=ai.get("base_url", defaults.ai_base_url),
            ai_api_key=raw_key,
            ai_timeout=ai.get("timeout", defaults.ai_timeout),
            ai_style=ai.get("style", defaults.ai_style),
            ai_fallback=ai.get("fallback_to_template", defaults.ai_fallback),
            display_animation=display.get("animation", defaults.display_animation),
            display_theme=display.get("theme", defaults.display_theme),
            reversal_prob=max(0.0, min(1.0, reversal.get("probability", defaults.reversal_prob))),
        )
