from nekomata.card.types import Arcana, Card, DrawnCard, Position


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


def test_drawn_card_status_label():
    card = Card(
        id="test", name="Test", name_zh="测试", arcana=Arcana.CUPS,
        number=1, element="water", astrology="Cancer",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
    )
    pos = Position(name="Past", name_zh="过去", description="过去的影响")
    assert DrawnCard(card=card, position=pos, is_reversed=False).status_label == "upright"
    assert DrawnCard(card=card, position=pos, is_reversed=True).status_label == "reversed"


def test_drawn_card_keywords_and_meaning():
    card = Card(
        id="test", name="Test", name_zh="测试", arcana=Arcana.CUPS,
        number=1, element="water", astrology="Cancer",
        keywords_upright=("正位关键词",), keywords_reversed=("逆位关键词",),
        meaning_upright="正位含义", meaning_reversed="逆位含义",
    )
    pos = Position(name="Past", name_zh="过去", description="过去的影响")
    upright = DrawnCard(card=card, position=pos, is_reversed=False)
    assert upright.keywords == ("正位关键词",)
    assert upright.meaning == "正位含义"
    reversed_dc = DrawnCard(card=card, position=pos, is_reversed=True)
    assert reversed_dc.keywords == ("逆位关键词",)
    assert reversed_dc.meaning == "逆位含义"
