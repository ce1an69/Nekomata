from datetime import datetime
from pathlib import Path
from uuid import uuid4

from nekomata.card.types import Arcana, Card, DrawnCard, Position, Reading
from nekomata.storage.journal import Journal


def make_reading(question: str = "测试问题") -> Reading:
    card = Card(
        id="major_00", name="The Fool", name_zh="愚者",
        arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
        keywords_upright=("新开始",), keywords_reversed=("鲁莽",),
        meaning_upright="新旅程", meaning_reversed="鲁莽",
    )
    pos = Position(name="Daily", name_zh="今日指引", description="今日灵感")
    return Reading(
        id=uuid4(),
        timestamp=datetime.now(),
        question=question,
        spread_name="Single Card",
        spread_name_zh="单牌",
        drawn_cards=[DrawnCard(card=card, position=pos, is_reversed=False)],
        interpretation="这是一个新的开始。",
    )


def test_save_and_load(tmp_path: Path):
    journal = Journal(tmp_path / "test.db")
    reading = make_reading()
    journal.save(reading)

    loaded = journal.load_recent(limit=1)
    assert len(loaded) == 1
    assert loaded[0].question == "测试问题"
    assert loaded[0].spread_name == "Single Card"
    assert loaded[0].interpretation == "这是一个新的开始。"


def test_load_recent_order(tmp_path: Path):
    journal = Journal(tmp_path / "test.db")
    for i in range(5):
        journal.save(make_reading(f"问题{i}"))
    loaded = journal.load_recent(limit=3)
    assert len(loaded) == 3
    assert loaded[0].question == "问题4"


def test_save_multiple_drawn_cards(tmp_path: Path):
    journal = Journal(tmp_path / "test.db")
    cards = [
        Card(
            id=f"major_{i:02d}", name=f"Card{i}", name_zh=f"牌{i}",
            arcana=Arcana.MAJOR, number=i, element="air", astrology="Uranus",
            keywords_upright=("a",), keywords_reversed=("b",),
            meaning_upright="up", meaning_reversed="down",
        )
        for i in range(3)
    ]
    positions = [
        Position("Past", "过去", "过去"),
        Position("Present", "现在", "现在"),
        Position("Future", "未来", "未来"),
    ]
    reading = Reading(
        id=uuid4(), timestamp=datetime.now(), question="三牌阵测试",
        spread_name="Past/Present/Future", spread_name_zh="过去·现在·未来",
        drawn_cards=[
            DrawnCard(card=c, position=p, is_reversed=i == 1)
            for i, (c, p) in enumerate(zip(cards, positions))
        ],
    )
    journal.save(reading)
    loaded = journal.load_recent(limit=1)
    assert len(loaded[0].drawn_cards) == 3
    assert loaded[0].drawn_cards[1].is_reversed is True


def test_init_creates_db(tmp_path: Path):
    db_path = tmp_path / "subdir" / "test.db"
    Journal(db_path)
    assert db_path.exists()
