from nekomata.card.deck import Deck
from nekomata.card.types import Card, Arcana
from nekomata.spread.single import SingleCardSpread
from nekomata.spread.three_card import PastPresentFuture, SituationActionResult, BodyMindSpirit
from nekomata.spread.five_card import FiveCardCross
from nekomata.spread import get_spread, SPREAD_REGISTRY


def make_deck(n: int = 10) -> Deck:
    cards = [
        Card(
            id=f"s_{i:02d}", name=f"S{i}", name_zh=f"牌{i}",
            arcana=Arcana.MAJOR, number=i, element="air", astrology="Uranus",
            keywords_upright=("a",), keywords_reversed=("b",),
            meaning_upright="up", meaning_reversed="down",
        )
        for i in range(n)
    ]
    return Deck(cards)


class TestSingleCardSpread:
    def test_name(self):
        s = get_spread("single")
        assert s.name == "Single Card"

    def test_position_count(self):
        assert len(get_spread("single").positions) == 1

    def test_draw(self):
        spread = get_spread("single")
        deck = make_deck()
        spread.draw(deck)
        assert len(spread.drawn_cards) == 1
        assert spread.drawn_cards[0].position.name == "Daily Guidance"
        assert deck.remaining == 9


class TestThreeCardSpreads:
    def test_past_present_future(self):
        s = get_spread("past_present_future")
        assert len(s.positions) == 3
        assert [p.name for p in s.positions] == ["Past", "Present", "Future"]

    def test_situation_action_result(self):
        s = get_spread("situation_action_result")
        assert len(s.positions) == 3
        assert [p.name for p in s.positions] == ["Situation", "Action", "Result"]

    def test_body_mind_spirit(self):
        s = get_spread("body_mind_spirit")
        assert len(s.positions) == 3
        assert [p.name for p in s.positions] == ["Body", "Mind", "Spirit"]

    def test_draw_three(self):
        spread = get_spread("past_present_future")
        deck = make_deck()
        spread.draw(deck)
        assert len(spread.drawn_cards) == 3
        assert deck.remaining == 7


def test_draw_populates_drawn_cards():
    spread = get_spread("single")
    assert len(spread.drawn_cards) == 0
    spread.draw(make_deck())
    assert len(spread.drawn_cards) == 1


def test_redraw_clears_previous():
    spread = get_spread("single")
    deck = make_deck(20)
    spread.draw(deck)
    first = spread.drawn_cards[0].card.id
    spread.draw(deck)
    second = spread.drawn_cards[0].card.id
    assert first != second


class TestFiveCardCross:
    def test_position_count(self):
        assert len(get_spread("five_card_cross").positions) == 5

    def test_draw(self):
        spread = get_spread("five_card_cross")
        deck = make_deck(10)
        spread.draw(deck)
        assert len(spread.drawn_cards) == 5
        assert deck.remaining == 5

    def test_position_names(self):
        assert [p.name for p in get_spread("five_card_cross").positions] == [
            "Present", "Challenge", "Foundation", "Past", "Guidance"
        ]


class TestSpreadRegistry:
    def test_registry_has_five_entries(self):
        assert len(SPREAD_REGISTRY) == 5

    def test_get_spread_returns_correct_type(self):
        assert isinstance(get_spread("single"), SingleCardSpread)
        assert isinstance(get_spread("past_present_future"), PastPresentFuture)
        with __import__("pytest").raises(KeyError):
            get_spread("nonexistent")

    def test_get_spread_raises_for_unknown_key(self):
        import pytest
        with pytest.raises(KeyError):
            get_spread("nonexistent")

    def test_registry_keys_match_get_spread(self):
        for key, cls in SPREAD_REGISTRY:
            assert isinstance(get_spread(key), cls)


def test_draw_raises_when_deck_too_small():
    """Spread.draw raises IndexError if deck has fewer cards than positions."""
    import pytest
    spread = get_spread("five_card_cross")
    deck = make_deck(3)
    with pytest.raises(IndexError, match="Need 5 cards"):
        spread.draw(deck)


def test_get_spread_injects_description():
    """get_spread sets the description from JSON."""
    spread = get_spread("single")
    assert spread.description
    assert spread.suitable_for
