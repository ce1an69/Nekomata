import random

import pytest

from nekomata.card.deck import Deck
from nekomata.card.types import Arcana, Card


def make_test_cards(n: int = 5) -> list[Card]:
    return [
        Card(
            id=f"test_{i:02d}", name=f"Card {i}", name_zh=f"测试{i}",
            arcana=Arcana.MAJOR, number=i, element="air", astrology="Uranus",
            keywords_upright=("a",), keywords_reversed=("b",),
            meaning_upright="up", meaning_reversed="down",
        )
        for i in range(n)
    ]


def test_deck_has_78_cards():
    deck = Deck()
    assert deck.remaining == 78


def test_deck_draw_reduces_count():
    deck = Deck(make_test_cards(5))
    deck.draw()
    assert deck.remaining == 4


def test_deck_draw_returns_card_and_reversal():
    deck = Deck(make_test_cards(5))
    card, is_reversed = deck.draw()
    assert isinstance(card, Card)
    assert isinstance(is_reversed, bool)


def test_deck_draw_all_exhausts():
    deck = Deck(make_test_cards(5))
    for _ in range(5):
        deck.draw()
    assert deck.remaining == 0
    with pytest.raises(IndexError):
        deck.draw()


def test_deck_draw_no_duplicates():
    deck = Deck()
    drawn_ids = set()
    for _ in range(78):
        card, _ = deck.draw()
        assert card.id not in drawn_ids
        drawn_ids.add(card.id)
    assert len(drawn_ids) == 78


def test_deck_shuffle_changes_order():
    cards = make_test_cards(20)
    random.seed(42)
    deck1 = Deck(cards)
    deck1.shuffle()
    order1 = [deck1.draw()[0].id for _ in range(20)]
    random.seed(99)
    deck2 = Deck(cards)
    deck2.shuffle()
    order2 = [deck2.draw()[0].id for _ in range(20)]
    assert order1 != order2


def test_deck_reversal_probability():
    deck = Deck(make_test_cards(1000))
    deck.shuffle()
    reversed_count = sum(1 for _ in range(1000) if deck.draw()[1])
    assert 400 < reversed_count < 600


def test_deck_reset():
    deck = Deck(make_test_cards(5))
    deck.draw()
    deck.draw()
    assert deck.remaining == 3
    deck.reset()
    assert deck.remaining == 5


def test_deck_draw_reversal_zero():
    """reversal_prob=0.0 should never produce reversed cards."""
    deck = Deck(make_test_cards(100))
    results = [deck.draw(reversal_prob=0.0)[1] for _ in range(100)]
    assert not any(results)


def test_deck_draw_reversal_one():
    """reversal_prob=1.0 should always produce reversed cards."""
    deck = Deck(make_test_cards(100))
    results = [deck.draw(reversal_prob=1.0)[1] for _ in range(100)]
    assert all(results)
