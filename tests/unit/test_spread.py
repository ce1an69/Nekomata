from nekomata.card.deck import Deck
from nekomata.card.types import Card, Arcana
from nekomata.spread.single import SingleCardSpread
from nekomata.spread.three_card import PastPresentFuture, SituationActionResult, BodyMindSpirit
from nekomata.spread.five_card import FiveCardCross
from nekomata.spread.celtic import CelticCross
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
        s = SingleCardSpread()
        assert s.name == "Single Card"
        assert s.name_zh == "单牌"

    def test_position_count(self):
        assert len(SingleCardSpread().positions) == 1

    def test_draw(self):
        spread = SingleCardSpread()
        deck = make_deck()
        spread.draw(deck)
        assert len(spread.drawn_cards) == 1
        assert spread.drawn_cards[0].position.name_zh == "今日指引"
        assert deck.remaining == 9


class TestThreeCardSpreads:
    def test_past_present_future(self):
        s = PastPresentFuture()
        assert len(s.positions) == 3
        assert [p.name_zh for p in s.positions] == ["过去", "现在", "未来"]

    def test_situation_action_result(self):
        s = SituationActionResult()
        assert len(s.positions) == 3
        assert [p.name_zh for p in s.positions] == ["处境", "行动", "结果"]

    def test_body_mind_spirit(self):
        s = BodyMindSpirit()
        assert len(s.positions) == 3
        assert [p.name_zh for p in s.positions] == ["身", "心", "灵"]

    def test_draw_three(self):
        spread = PastPresentFuture()
        deck = make_deck()
        spread.draw(deck)
        assert len(spread.drawn_cards) == 3
        assert deck.remaining == 7


def test_draw_populates_drawn_cards():
    spread = SingleCardSpread()
    assert len(spread.drawn_cards) == 0
    spread.draw(make_deck())
    assert len(spread.drawn_cards) == 1


def test_redraw_clears_previous():
    spread = SingleCardSpread()
    deck = make_deck(20)
    spread.draw(deck)
    first = spread.drawn_cards[0].card.id
    spread.draw(deck)
    second = spread.drawn_cards[0].card.id
    assert first != second


class TestFiveCardCross:
    def test_position_count(self):
        assert len(FiveCardCross().positions) == 5

    def test_draw(self):
        spread = FiveCardCross()
        deck = make_deck(10)
        spread.draw(deck)
        assert len(spread.drawn_cards) == 5
        assert deck.remaining == 5

    def test_position_names(self):
        assert [p.name_zh for p in FiveCardCross().positions] == [
            "现状", "挑战", "根基", "过去", "指引"
        ]


class TestCelticCross:
    def test_position_count(self):
        assert len(CelticCross().positions) == 10

    def test_draw(self):
        spread = CelticCross()
        deck = make_deck(15)
        spread.draw(deck)
        assert len(spread.drawn_cards) == 10
        assert deck.remaining == 5

    def test_position_names(self):
        names = [p.name_zh for p in CelticCross().positions]
        assert names[0] == "当前处境"
        assert names[9] == "最终结果"


class TestSpreadRegistry:
    def test_registry_has_five_entries(self):
        assert len(SPREAD_REGISTRY) == 5
        assert all(key != "celtic_cross" for key, _, _ in SPREAD_REGISTRY)

    def test_get_spread_returns_correct_type(self):
        assert isinstance(get_spread("single"), SingleCardSpread)
        assert isinstance(get_spread("past_present_future"), PastPresentFuture)
        import pytest
        with pytest.raises(KeyError):
            get_spread("celtic_cross")

    def test_get_spread_raises_for_unknown_key(self):
        import pytest
        with pytest.raises(KeyError):
            get_spread("nonexistent")

    def test_registry_keys_match_get_spread(self):
        for key, _, cls in SPREAD_REGISTRY:
            assert isinstance(get_spread(key), cls)


def test_draw_raises_when_deck_too_small():
    """Spread.draw raises IndexError if deck has fewer cards than positions."""
    import pytest
    spread = CelticCross()  # requires 10 cards
    deck = make_deck(5)     # only 5 cards
    with pytest.raises(IndexError, match="Need 10 cards"):
        spread.draw(deck)


def test_get_spread_injects_description():
    """get_spread sets the description from the registry."""
    spread = get_spread("single")
    assert spread.description == "每日灵感"
