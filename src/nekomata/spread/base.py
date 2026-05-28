"""Base class for all tarot card spreads."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nekomata.card.types import DrawnCard, Position

if TYPE_CHECKING:
    from nekomata.card.deck import Deck


class Spread:
    """Base class for all tarot card spreads.

    All copy (name, description, positions, suitable_for) and
    ``display_order`` are loaded from locale JSON by the registry.
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
        return self._positions

    @positions.setter
    def positions(self, value: list[Position]) -> None:
        self._positions = value
        self._display_order = None

    @property
    def display_order(self) -> tuple[int, ...]:
        if self._display_order is None:
            self._display_order = tuple(range(len(self._positions)))
        return self._display_order

    @display_order.setter
    def display_order(self, value: tuple[int, ...]) -> None:
        self._display_order = value

    def draw(self, deck: Deck, reversal_prob: float = 0.5) -> list[DrawnCard]:
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
