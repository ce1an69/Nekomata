from __future__ import annotations

from nekomata.card.deck import Deck
from nekomata.card.types import DrawnCard, Position


class Spread:
    name: str = ""
    name_zh: str = ""

    def __init__(self) -> None:
        self._drawn_cards: list[DrawnCard] = []
        self._positions: list[Position] = []

    @property
    def positions(self) -> list[Position]:
        return self._positions

    @property
    def drawn_cards(self) -> list[DrawnCard]:
        return list(self._drawn_cards)

    def draw(self, deck: Deck) -> None:
        self._drawn_cards.clear()
        for pos in self._positions:
            card, is_reversed = deck.draw()
            self._drawn_cards.append(
                DrawnCard(card=card, position=pos, is_reversed=is_reversed)
            )
