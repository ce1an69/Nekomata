from nekomata.card.types import Arcana, Card, DrawnCard, Position, Reading


def test_arcana_values():
    assert set(Arcana) == {
        Arcana.MAJOR, Arcana.CUPS, Arcana.WANDS, Arcana.SWORDS, Arcana.PENTACLES
    }


def test_arcana_is_str():
    assert Arcana.MAJOR == "major"
    assert Arcana.CUPS == "cups"


def test_card_creation():
    card = Card(
        id="major_00", name="The Fool", name_zh="愚者",
        arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
        keywords_upright=("新开始", "天真", "冒险"),
        keywords_reversed=("鲁莽", "冒失", "停滞"),
        meaning_upright="一段新旅程的开始。",
        meaning_reversed="过于鲁莽。",
    )
    assert card.id == "major_00"
    assert card.arcana == Arcana.MAJOR
    assert len(card.keywords_upright) == 3


def test_card_frozen():
    card = Card(
        id="test", name="Test", name_zh="测试", arcana=Arcana.MAJOR,
        number=0, element="air", astrology="Uranus",
        keywords_upright=(), keywords_reversed=(),
        meaning_upright="up", meaning_reversed="down",
    )
    try:
        card.name = "changed"
        assert False, "Should be frozen"
    except AttributeError:
        pass


def test_position():
    pos = Position(name="Present", name_zh="现在", description="当前状况")
    assert pos.name_zh == "现在"


def test_drawn_card():
    card = Card(
        id="test", name="Test", name_zh="测试", arcana=Arcana.CUPS,
        number=1, element="water", astrology="Cancer",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
    )
    pos = Position(name="Past", name_zh="过去", description="过去的影响")
    dc = DrawnCard(card=card, position=pos, is_reversed=True)
    assert dc.is_reversed is True
    assert dc.card.name_zh == "测试"
    assert dc.position.name == "Past"


def test_reading():
    from datetime import datetime
    from uuid import uuid4

    reading = Reading(
        id=uuid4(),
        timestamp=datetime.now(),
        question="今天运势如何？",
        spread_name="Single Card",
        spread_name_zh="单牌",
        drawn_cards=[],
    )
    assert reading.interpretation is None
    assert reading.question == "今天运势如何？"
