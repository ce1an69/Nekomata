from __future__ import annotations

from pathlib import Path

import yaml

from nekomata.card.types import Arcana, Card


def load_card_meanings(path: Path | None = None) -> list[dict]:
    if path is None:
        path = Path(__file__).resolve().parents[3] / "data" / "card_meanings.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all_cards(path: Path | None = None) -> list[Card]:
    entries = load_card_meanings(path)
    cards = []
    for e in entries:
        cards.append(Card(
            id=e["id"],
            name=e["name"],
            name_zh=e["name_zh"],
            arcana=Arcana(e["arcana"]),
            number=e["number"],
            element=e["element"],
            astrology=e["astrology"],
            keywords_upright=tuple(e["keywords_upright"]),
            keywords_reversed=tuple(e["keywords_reversed"]),
            meaning_upright=e["meaning_upright"],
            meaning_reversed=e["meaning_reversed"],
        ))
    return cards
