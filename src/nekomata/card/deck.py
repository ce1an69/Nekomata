"""Tarot deck: shuffle, draw, and reset the 78-card deck."""


import random

from nekomata.card.data import load_all_cards
from nekomata.card.types import Card


class Deck:
    """A shuffled tarot deck that supports drawing cards one at a time."""

    def __init__(self, cards: list[Card] | None = None):
        if cards is None:
            cards = load_all_cards()
        self._original = list(cards)
        self._cards = list(cards)

    @property
    def remaining(self) -> int:
        """Number of cards left in the deck."""
        return len(self._cards)

    def shuffle(self) -> None:
        """Randomize the order of remaining cards."""
        random.shuffle(self._cards)

    def draw(self, reversal_prob: float = 0.5) -> tuple[Card, bool]:
        """Draw the top card. Returns (card, is_reversed)."""
        if not self._cards:
            raise IndexError("No cards left in deck")
        card = self._cards.pop()
        is_reversed = random.random() < reversal_prob
        return card, is_reversed

    def reset(self) -> None:
        """Restore the deck to its original (unshuffled) state."""
        self._cards = list(self._original)
