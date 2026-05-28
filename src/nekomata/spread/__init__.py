"""Spread registry and factory for all tarot card layouts."""

from nekomata.card.types import Position
from nekomata.i18n import spread_strings
from nekomata.spread.base import Spread

# Ordered registry: key → display order (None = default sequential)
_SPREAD_DEFS: list[tuple[str, tuple[int, ...] | None]] = [
    ("single", None),
    ("past_present_future", None),
    ("situation_action_result", None),
    ("body_mind_spirit", None),
    ("five_card_cross", (3, 0, 2, 1, 4)),
]

SPREAD_REGISTRY: list[tuple[str, type[Spread]]] = [
    (key, Spread) for key, _ in _SPREAD_DEFS
]
_SPREAD_MAP: dict[str, tuple[int, ...] | None] = {
    key: order for key, order in _SPREAD_DEFS
}


def get_spread(key: str) -> Spread:
    """Create a Spread instance by registry key, loading copy from locale."""
    if key not in _SPREAD_MAP:
        raise KeyError(f"Unknown spread: {key}")
    spread = Spread()
    data = spread_strings()["spreads"][key]
    spread.name = data["name"]
    spread.description = data["description"]
    spread.suitable_for = data.get("suitable_for", "")
    spread.positions = [
        Position(name=p["name"], name_zh="", description=p["description"])
        for p in data["positions"]
    ]
    order = _SPREAD_MAP[key]
    if order is not None:
        spread.display_order = order
    return spread
