from nekomata.card.deck import Deck
from nekomata.card.types import Card, Arcana
from nekomata.spread.single import SingleCardSpread
from nekomata.spread.three_card import PastPresentFuture, SituationActionResult


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
