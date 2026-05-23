"""Spread registry and factory for all tarot card layouts."""

import json

from nekomata._paths import data_dir as _data_dir_func
from nekomata.card.types import Position
from nekomata.spread.base import Spread
from nekomata.spread.single import SingleCardSpread
from nekomata.spread.three_card import PastPresentFuture, SituationActionResult, BodyMindSpirit
from nekomata.spread.five_card import FiveCardCross

_DATA_DIR = _data_dir_func()

# Ordered registry: (key, class) — order matters for UI index-based selection
SPREAD_REGISTRY: list[tuple[str, type[Spread]]] = [
    ("single", SingleCardSpread),
    ("past_present_future", PastPresentFuture),
    ("situation_action_result", SituationActionResult),
    ("body_mind_spirit", BodyMindSpirit),
    ("five_card_cross", FiveCardCross),
]

# O(1) lookup map built from the ordered registry
_SPREAD_MAP: dict[str, type[Spread]] = {key: cls for key, cls in SPREAD_REGISTRY}


def _load_strings() -> dict:
    """Load spread_strings.json once."""
    path = _DATA_DIR / "spread_strings.json"
    return json.loads(path.read_text(encoding="utf-8"))["spreads"]


_SPREAD_STRINGS = _load_strings()


def get_spread(key: str) -> Spread:
    """Create a Spread instance by registry key, loading copy from JSON."""
    cls = _SPREAD_MAP.get(key)
    if cls is None:
        raise KeyError(f"Unknown spread: {key}")
    spread = cls()
    data = _SPREAD_STRINGS[key]
    spread.name = data["name"]
    spread.description = data["description"]
    spread.suitable_for = data.get("suitable_for", "")
    spread.positions = [
        Position(name=p["name"], name_zh="", description=p["description"])
        for p in data["positions"]
    ]
    return spread
