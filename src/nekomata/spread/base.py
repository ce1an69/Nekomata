"""Base class for all tarot card spreads."""


from __future__ import annotations

from typing import TYPE_CHECKING

from nekomata.card.types import DrawnCard, Position

if TYPE_CHECKING:
    from nekomata.card.deck import Deck


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
        self.drawn_cards: list[DrawnCard] = []

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

    def draw(self, deck: Deck, reversal_prob: float = 0.5) -> list[DrawnCard]:
        """Draw cards from *deck* for each position in this spread."""
        n = len(self._positions)
        if deck.remaining < n:
            raise IndexError(f"Need {n} cards")
        self.drawn_cards = []
        for position in self._positions:
            card, is_reversed = deck.draw(reversal_prob)
            self.drawn_cards.append(
                DrawnCard(card=card, position=position, is_reversed=is_reversed)
            )
        return self.drawn_cards
