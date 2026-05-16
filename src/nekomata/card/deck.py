from __future__ import annotations

import random

from nekomata.card.types import Card


class Deck:
    def __init__(self, cards: list[Card] | None = None):
        if cards is None:
            from nekomata.card.data import load_all_cards
            cards = load_all_cards()
        self._original = list(cards)
        self._cards = list(cards)

    @property
    def remaining(self) -> int:
        return len(self._cards)

    def shuffle(self) -> None:
        random.shuffle(self._cards)

    def draw(self, reversal_prob: float = 0.5) -> tuple[Card, bool]:
        if not self._cards:
            raise IndexError("No cards left in deck")
        card = self._cards.pop()
        is_reversed = random.random() < reversal_prob
        return card, is_reversed

    def reset(self) -> None:
        self._cards = list(self._original)
