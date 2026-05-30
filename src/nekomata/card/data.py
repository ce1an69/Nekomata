"""Load and cache all 78 card definitions from YAML + resolve PNG image paths."""

import functools
from pathlib import Path

import yaml

from nekomata._paths import assets_dir, data_dir
from nekomata.card.types import Arcana, Card


def _resolve_image_path(card_id: str, arcana: Arcana) -> Path | None:
    """Check if a card PNG exists in assets/cards/{arcana}/{id}.png."""
    png_path = assets_dir() / "cards" / arcana.value / f"{card_id}.png"
    return png_path if png_path.exists() else None


def _load_card_meanings(path: Path | None = None) -> list[dict]:
    """Parse the YAML card meanings file into raw dicts."""
    if path is None:
        path = data_dir() / "card_meanings.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _build_card(e: dict) -> Card:
    """Build a single Card from a parsed YAML entry dict."""
    arcana = Arcana(e["arcana"])
    return Card(
        id=e["id"],
        name=e["name"],
        name_zh=e["name_zh"],
        arcana=arcana,
        number=e["number"],
        element=e["element"],
        astrology=e["astrology"],
        keywords_upright=tuple(e["keywords_upright"]),
        keywords_reversed=tuple(e["keywords_reversed"]),
        meaning_upright=e["meaning_upright"],
        meaning_reversed=e["meaning_reversed"],
        image_path=_resolve_image_path(e["id"], arcana),
        keywords_upright_en=tuple(e.get("keywords_upright_en", [])),
        keywords_reversed_en=tuple(e.get("keywords_reversed_en", [])),
        meaning_upright_en=e.get("meaning_upright_en", ""),
        meaning_reversed_en=e.get("meaning_reversed_en", ""),
    )


@functools.lru_cache(maxsize=1)
def _load_default_cards() -> list[Card]:
    """Build Card objects from the default YAML (cached)."""
    return [_build_card(e) for e in _load_card_meanings()]


def load_all_cards(path: Path | None = None) -> list[Card]:
    """Load all 78 cards from YAML. Default path is cached via lru_cache."""
    if path is None:
        return _load_default_cards()
    # Custom path — build fresh each time (not cached)
    return [_build_card(e) for e in _load_card_meanings(path)]
