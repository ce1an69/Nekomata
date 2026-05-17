"""Tests for the SQLite-backed journal storage."""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from nekomata.card.types import Arcana, Card, DrawnCard, Position, Reading
from nekomata.storage.journal import Journal, _row_to_reading


def _make_card(card_id: str = "test_card") -> Card:
    return Card(
        id=card_id, name="Test Card", name_zh="测试牌",
        arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
    )


def _make_reading(**overrides) -> Reading:
    pos = Position(name="Past", name_zh="过去", description="过去的影响")
    drawn = [DrawnCard(card=_make_card(), position=pos, is_reversed=False)]
    defaults = dict(
        question="测试问题",
        spread_name="Single Card",
        spread_name_zh="单牌",
        drawn_cards=drawn,
        interpretation="测试解读",
    )
    defaults.update(overrides)
    return Reading(**defaults)


def test_save_and_get():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        journal = Journal(db_path)
        reading = _make_reading()
        journal.save(reading)

        fetched = journal.get(reading.id)
        assert fetched is not None
        assert fetched.question == "测试问题"
        assert fetched.spread_name == "Single Card"
        assert fetched.interpretation == "测试解读"
        assert len(fetched.drawn_cards) == 1
        assert fetched.drawn_cards[0].card.id == "test_card"
        assert fetched.drawn_cards[0].is_reversed is False
    finally:
        db_path.unlink(missing_ok=True)


def test_get_nonexistent():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        journal = Journal(db_path)
        assert journal.get(uuid4()) is None
    finally:
        db_path.unlink(missing_ok=True)


def test_list_recent_ordering():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        journal = Journal(db_path)
        r1 = _make_reading(question="第一条")
        r2 = _make_reading(question="第二条")
        journal.save(r1)
        journal.save(r2)

        recent = journal.list_recent(limit=10)
        assert len(recent) == 2
        assert recent[0].question == "第二条"
        assert recent[1].question == "第一条"
    finally:
        db_path.unlink(missing_ok=True)


def test_list_recent_limit():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        journal = Journal(db_path)
        for i in range(5):
            journal.save(_make_reading(question=f"Q{i}"))

        recent = journal.list_recent(limit=3)
        assert len(recent) == 3
    finally:
        db_path.unlink(missing_ok=True)


def test_delete():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        journal = Journal(db_path)
        reading = _make_reading()
        journal.save(reading)
        assert journal.count() == 1

        assert journal.delete(reading.id) is True
        assert journal.count() == 0
        assert journal.get(reading.id) is None
    finally:
        db_path.unlink(missing_ok=True)


def test_delete_nonexistent():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        journal = Journal(db_path)
        assert journal.delete(uuid4()) is False
    finally:
        db_path.unlink(missing_ok=True)


def test_count():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        journal = Journal(db_path)
        assert journal.count() == 0
        journal.save(_make_reading())
        assert journal.count() == 1
        journal.save(_make_reading(question="another"))
        assert journal.count() == 2
    finally:
        db_path.unlink(missing_ok=True)


def test_drawn_cards_serialization():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        journal = Journal(db_path)
        pos1 = Position(name="Past", name_zh="过去", description="过去的影响")
        pos2 = Position(name="Future", name_zh="未来", description="可能的发展")
        drawn = [
            DrawnCard(card=_make_card("card_a"), position=pos1, is_reversed=False),
            DrawnCard(card=_make_card("card_b"), position=pos2, is_reversed=True),
        ]
        reading = _make_reading(drawn_cards=drawn)
        journal.save(reading)

        fetched = journal.get(reading.id)
        assert len(fetched.drawn_cards) == 2
        assert fetched.drawn_cards[0].position.name_zh == "过去"
        assert fetched.drawn_cards[1].is_reversed is True
    finally:
        db_path.unlink(missing_ok=True)


def test_stored_card_names_preserved():
    """Card names are stored in JSON and restored on load."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        journal = Journal(db_path)
        card = Card(
            id="the_fool", name="The Fool", name_zh="愚者",
            arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
            keywords_upright=(), keywords_reversed=(),
            meaning_upright="", meaning_reversed="",
        )
        pos = Position(name="Past", name_zh="过去", description="")
        drawn = [DrawnCard(card=card, position=pos, is_reversed=True)]
        journal.save(_make_reading(drawn_cards=drawn))

        fetched = journal.list_recent()[0]
        assert fetched.drawn_cards[0].card.name == "The Fool"
        assert fetched.drawn_cards[0].card.name_zh == "愚者"
    finally:
        db_path.unlink(missing_ok=True)


def test_corrupt_drawn_cards_json():
    """Malformed JSON in drawn_cards yields an empty card list, not a crash."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE readings (
                id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, question TEXT NOT NULL,
                spread_name TEXT NOT NULL, spread_name_zh TEXT NOT NULL,
                drawn_cards TEXT NOT NULL, interpretation TEXT
            )
        """)
        conn.execute(
            "INSERT INTO readings VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid4()), datetime.now().isoformat(), "Q", "S", "牌阵", "NOT JSON", None),
        )
        conn.row_factory = sqlite3.Row
        conn.commit()
        row = conn.execute("SELECT * FROM readings").fetchone()
        conn.close()

        reading = _row_to_reading(row)
        assert reading.drawn_cards == []
    finally:
        db_path.unlink(missing_ok=True)


def test_corrupt_card_entry_skipped():
    """A single corrupt card entry is skipped without breaking the rest."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        bad_cards = json.dumps([
            {"card_id": "ok", "card_name": "OK", "card_name_zh": "好",
             "position_name": "P", "position_name_zh": "P", "position_desc": "", "is_reversed": False},
            {"missing_keys": True},
        ])
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE readings (
                id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, question TEXT NOT NULL,
                spread_name TEXT NOT NULL, spread_name_zh TEXT NOT NULL,
                drawn_cards TEXT NOT NULL, interpretation TEXT
            )
        """)
        conn.execute(
            "INSERT INTO readings VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid4()), datetime.now().isoformat(), "Q", "S", "牌阵", bad_cards, None),
        )
        conn.row_factory = sqlite3.Row
        conn.commit()
        row = conn.execute("SELECT * FROM readings").fetchone()
        conn.close()

        reading = _row_to_reading(row)
        assert len(reading.drawn_cards) == 1
        assert reading.drawn_cards[0].card.id == "ok"
    finally:
        db_path.unlink(missing_ok=True)


def test_arcana_preserved_through_save_load():
    """Card arcana and number are preserved when saving and loading."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        journal = Journal(db_path)
        pos = Position(name="Past", name_zh="过去", description="")
        cups_card = Card(
            id="cups_01", name="Ace of Cups", name_zh="圣杯一",
            arcana=Arcana.CUPS, number=1, element="water", astrology="Cancer",
            keywords_upright=(), keywords_reversed=(),
            meaning_upright="", meaning_reversed="",
        )
        swords_card = Card(
            id="swords_07", name="Seven of Swords", name_zh="宝剑七",
            arcana=Arcana.SWORDS, number=7, element="air", astrology="Aquarius",
            keywords_upright=(), keywords_reversed=(),
            meaning_upright="", meaning_reversed="",
        )
        drawn = [
            DrawnCard(card=cups_card, position=pos, is_reversed=False),
            DrawnCard(card=swords_card, position=pos, is_reversed=True),
        ]
        journal.save(_make_reading(drawn_cards=drawn))

        fetched = journal.list_recent()[0]
        assert fetched.drawn_cards[0].card.arcana == Arcana.CUPS
        assert fetched.drawn_cards[0].card.number == 1
        assert fetched.drawn_cards[1].card.arcana == Arcana.SWORDS
        assert fetched.drawn_cards[1].card.number == 7
    finally:
        db_path.unlink(missing_ok=True)


def test_invalid_arcana_value_skipped():
    """A card entry with an invalid arcana value is skipped gracefully."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        bad_cards = json.dumps([
            {"card_id": "bad", "card_name": "Bad", "card_name_zh": "坏",
             "card_arcana": "not_a_real_arcana", "card_number": 0,
             "position_name": "P", "position_name_zh": "P", "position_desc": "",
             "is_reversed": False},
            {"card_id": "ok", "card_name": "OK", "card_name_zh": "好",
             "card_arcana": "cups", "card_number": 1,
             "position_name": "P", "position_name_zh": "P", "position_desc": "",
             "is_reversed": False},
        ])
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE readings (
                id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, question TEXT NOT NULL,
                spread_name TEXT NOT NULL, spread_name_zh TEXT NOT NULL,
                drawn_cards TEXT NOT NULL, interpretation TEXT
            )
        """)
        conn.execute(
            "INSERT INTO readings VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid4()), datetime.now().isoformat(), "Q", "S", "牌阵", bad_cards, None),
        )
        conn.row_factory = sqlite3.Row
        conn.commit()
        row = conn.execute("SELECT * FROM readings").fetchone()
        conn.close()

        reading = _row_to_reading(row)
        assert len(reading.drawn_cards) == 1
        assert reading.drawn_cards[0].card.arcana == Arcana.CUPS
    finally:
        db_path.unlink(missing_ok=True)
