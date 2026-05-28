"""Style consistency checks for the Web UI."""

from pathlib import Path


STATIC_DIR = Path(__file__).parents[2] / "src" / "nekomata" / "web" / "static"
STYLE_FILES = [
    "base.css",
    "components.css",
    "screens.css",
    "slots.css",
    "animations.css",
    "draw.js",
]


def _static_text() -> str:
    return "\n".join((STATIC_DIR / name).read_text(encoding="utf-8") for name in STYLE_FILES)


def test_web_accent_is_catppuccin_mauve():
    css = (STATIC_DIR / "base.css").read_text(encoding="utf-8")

    assert "--accent: #cba6f7;" in css
    assert "rgba(203, 166, 247" in css


def test_web_styles_do_not_use_gold_accent_naming():
    text = _static_text().lower()

    assert "gold" not in text
    assert "--accent" in text
