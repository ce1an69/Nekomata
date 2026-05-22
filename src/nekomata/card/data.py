"""Load and cache all 78 card definitions from YAML + resolve PNG image paths."""


from pathlib import Path

import yaml

from nekomata.card.types import Arcana, Card

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
ASSETS_DIR = _PROJECT_ROOT / "assets" / "cards"

# Module-level cache to avoid re-parsing YAML on repeated calls
_cards_cache: list[Card] | None = None


def _load_card_meanings(path: Path | None = None) -> list[dict]:
    """Parse the YAML card meanings file into raw dicts."""
    if path is None:
        path = _PROJECT_ROOT / "data" / "card_meanings.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_image_path(card_id: str, arcana: Arcana) -> Path | None:
    """Check if a card PNG exists in assets/cards/{arcana}/{id}.png."""
    png_path = ASSETS_DIR / arcana.value / f"{card_id}.png"
    return png_path if png_path.exists() else None


def load_all_cards(path: Path | None = None) -> list[Card]:
    """Load all 78 cards from YAML. Results are cached after first call."""
    global _cards_cache
    if _cards_cache is not None and path is None:
        return _cards_cache
    entries = _load_card_meanings(path)
    cards = []
    for e in entries:
        arcana = Arcana(e["arcana"])
        cards.append(Card(
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
        ))
    if path is None:
        _cards_cache = cards
    return cards
