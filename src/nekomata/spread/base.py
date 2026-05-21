"""Base class for all tarot card spreads."""


from nekomata.card.types import Position


class Spread:
    """Base class for all tarot card spreads.

    Subclasses define ``name`` (used as JSON lookup key) and ``display_order``.
    All copy (description, positions, suitable_for) is loaded from
    ``data/spread_strings.json`` by the registry in ``__init__``.
    """

    name: str = ""
    description: str = ""
    suitable_for: str = ""

    def __init__(self) -> None:
        self._positions: list[Position] = []

    @property
    def positions(self) -> list[Position]:
        """The positional slots this spread defines."""
        return self._positions

    @property
    def display_order(self) -> list[int]:
        """Visual layout order for grid display. Override for custom layouts."""
        return list(range(len(self._positions)))
