"""Base class for all tarot card spreads."""


from nekomata.card.deck import Deck
from nekomata.card.types import DrawnCard, Position


class Spread:
    """Base class for all tarot card spreads."""

    name: str = ""
    name_zh: str = ""
    description: str = ""

    def __init__(self) -> None:
        self._drawn_cards: list[DrawnCard] = []
        self._positions: list[Position] = []

    @property
    def positions(self) -> list[Position]:
        """The positional slots this spread defines."""
        return self._positions

    @property
    def drawn_cards(self) -> list[DrawnCard]:
        """Cards drawn into this spread (copy to prevent mutation)."""
        return list(self._drawn_cards)

    def draw(self, deck: Deck, reversal_prob: float = 0.5) -> None:
        """Draw one card per position from the deck, clearing any previous draw.

        Raises IndexError if the deck has fewer cards than positions.
        """
        if deck.remaining < len(self._positions):
            raise IndexError(
                f"Need {len(self._positions)} cards but deck has {deck.remaining}"
            )
        self._drawn_cards.clear()
        for pos in self._positions:
            card, is_reversed = deck.draw(reversal_prob)
            self._drawn_cards.append(
                DrawnCard(card=card, position=pos, is_reversed=is_reversed)
            )
