from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    ai_backend: str = "template"
    ai_model: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str | None = None
    ai_timeout: float = 60.0
    ai_style: str = "mystical"
    ai_max_retries: int = 2
    ai_fallback: bool = True
    display_animation: bool = True
    display_theme: str = "dark"
    reversal_prob: float = 0.5

    @classmethod
    def load(cls, path: Path | None = None) -> AppConfig:
        defaults = cls()
        if path is None:
            path = Path("config.toml")
        if not path.exists():
            return defaults
        with open(path, "rb") as f:
            data = tomllib.load(f)

        ai = data.get("ai", {})
        display = data.get("display", {})
        reversal = data.get("reversal", {})

        return cls(
            ai_backend=ai.get("backend", defaults.ai_backend),
            ai_model=ai.get("model", defaults.ai_model),
            ai_base_url=ai.get("base_url", defaults.ai_base_url),
            ai_api_key=ai.get("api_key", defaults.ai_api_key),
            ai_timeout=ai.get("timeout", defaults.ai_timeout),
            ai_style=ai.get("style", defaults.ai_style),
            ai_max_retries=ai.get("max_retries", defaults.ai_max_retries),
            ai_fallback=ai.get("fallback_to_template", defaults.ai_fallback),
            display_animation=display.get("animation", defaults.display_animation),
            display_theme=display.get("theme", defaults.display_theme),
            reversal_prob=reversal.get("probability", defaults.reversal_prob),
        )
