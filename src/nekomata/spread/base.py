"""Base class for all tarot card spreads."""


from nekomata.card.types import Position


class Spread:
    """Base class for all tarot card spreads.

    Subclasses define ``display_order``.
    All copy (name, description, positions, suitable_for) is loaded from
    ``data/spread_strings.json`` by the registry in ``__init__``.
    """

    name: str = ""
    description: str = ""
    suitable_for: str = ""

    def __init__(self) -> None:
        self._positions: list[Position] = []
        self._display_order: tuple[int, ...] | None = None

    @property
    def positions(self) -> list[Position]:
        """The positional slots this spread defines."""
        return self._positions

    @positions.setter
    def positions(self, value: list[Position]) -> None:
        self._positions = value
        self._display_order = None  # invalidate cache

    @property
    def display_order(self) -> tuple[int, ...]:
        """Visual layout order for grid display. Override for custom layouts."""
        if self._display_order is None:
            self._display_order = tuple(range(len(self._positions)))
        return self._display_order
