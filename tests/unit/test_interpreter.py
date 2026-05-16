from nekomata.card.types import Arcana, Card, DrawnCard, Position
from nekomata.ai.interpreter import template_interpret


def make_drawn_cards(n: int, reversed_idx: set[int] | None = None) -> list[DrawnCard]:
    reversed_idx = reversed_idx or set()
    positions = [
        Position("Past", "过去", "过去的影响"),
        Position("Present", "现在", "当前状况"),
        Position("Future", "未来", "未来发展"),
    ]
    return [
        DrawnCard(
            card=Card(
                id=f"major_{i:02d}", name=f"Card{i}", name_zh=f"牌{i}",
                arcana=Arcana.MAJOR, number=i, element="air", astrology="Uranus",
                keywords_upright=(f"正位关键词{i}",),
                keywords_reversed=(f"逆位关键词{i}",),
                meaning_upright=f"正位含义{i}",
                meaning_reversed=f"逆位含义{i}",
            ),
            position=positions[i],
            is_reversed=(i in reversed_idx),
        )
        for i in range(n)
    ]


def test_template_interpret_contains_question():
    assert "今天运势如何？" in template_interpret(make_drawn_cards(1), "今天运势如何？")


def test_template_interpret_single_card():
    result = template_interpret(make_drawn_cards(1), "test")
    assert "牌0" in result
    assert "正位关键词0" in result


def test_template_interpret_reversed():
    result = template_interpret(make_drawn_cards(3, reversed_idx={1}), "test")
    assert "逆位" in result
    assert "逆位关键词1" in result


def test_template_interpret_three_cards():
    result = template_interpret(make_drawn_cards(3), "三牌阵测试")
    assert "过去" in result
    assert "现在" in result
    assert "未来" in result
