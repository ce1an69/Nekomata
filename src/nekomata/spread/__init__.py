"""Spread registry and factory for all tarot card layouts."""

import json
from pathlib import Path

from nekomata.card.types import Position
from nekomata.spread.base import Spread
from nekomata.spread.single import SingleCardSpread
from nekomata.spread.three_card import PastPresentFuture, SituationActionResult, BodyMindSpirit
from nekomata.spread.five_card import FiveCardCross

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"

# Ordered registry: (key, class)
SPREAD_REGISTRY: list[tuple[str, type[Spread]]] = [
    ("single", SingleCardSpread),
    ("past_present_future", PastPresentFuture),
    ("situation_action_result", SituationActionResult),
    ("body_mind_spirit", BodyMindSpirit),
    ("five_card_cross", FiveCardCross),
]


def _load_strings() -> dict:
    """Load spread_strings.json once."""
    path = _DATA_DIR / "spread_strings.json"
    return json.loads(path.read_text(encoding="utf-8"))["spreads"]


_SPREAD_STRINGS = _load_strings()


def get_spread(key: str) -> Spread:
    """Create a Spread instance by registry key, loading copy from JSON."""
    for registry_key, cls in SPREAD_REGISTRY:
        if registry_key == key:
            spread = cls()
            data = _SPREAD_STRINGS[key]
            spread.name = data["name"]
            spread.description = data["description"]
            spread.suitable_for = data.get("suitable_for", "")
            spread._positions = [
                Position(name=p["name"], name_zh="", description=p["description"])
                for p in data["positions"]
            ]
            return spread
    raise KeyError(f"Unknown spread: {key}")
