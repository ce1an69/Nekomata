"""SQLite-backed journal for storing and retrieving tarot readings."""


import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import UUID

from nekomata.card.types import (
    Arcana, Card, DrawnCard, Position, Reading,
)

log = logging.getLogger(__name__)

# Default database path, next to config.toml
_DB_PATH = Path(__file__).resolve().parents[3] / "journal.db"


def _connect(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or _DB_PATH
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            question TEXT NOT NULL,
            spread_name TEXT NOT NULL,
            spread_name_zh TEXT NOT NULL,
            drawn_cards TEXT NOT NULL,
            interpretation TEXT
        )
    """)
    conn.commit()
    return conn


def _serialize_drawn_cards(cards: list[DrawnCard]) -> str:
    """Serialize drawn cards to JSON for storage."""
    return json.dumps([
        {
            "card_id": dc.card.id,
            "card_name": dc.card.name,
            "card_name_zh": dc.card.name_zh,
            "card_arcana": dc.card.arcana.value,
            "card_number": dc.card.number,
            "position_name": dc.position.name,
            "position_name_zh": dc.position.name_zh,
            "position_desc": dc.position.description,
            "is_reversed": dc.is_reversed,
        }
        for dc in cards
    ])


class Journal:
    """SQLite-backed store for completed tarot readings."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._path = db_path or _DB_PATH

    def _connect(self) -> sqlite3.Connection:
        return _connect(self._path)

    def save(self, reading: Reading) -> None:
        """Persist a reading to the journal."""
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO readings
                   (id, timestamp, question, spread_name, spread_name_zh, drawn_cards, interpretation)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(reading.id),
                    reading.timestamp.isoformat(),
                    reading.question,
                    reading.spread_name,
                    reading.spread_name_zh,
                    _serialize_drawn_cards(reading.drawn_cards),
                    reading.interpretation,
                ),
            )

    def list_recent(self, limit: int = 20) -> list[Reading]:
        """Return the most recent readings, newest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM readings ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_row_to_reading(r) for r in rows]

    def get(self, reading_id: UUID) -> Reading | None:
        """Fetch a single reading by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM readings WHERE id = ?", (str(reading_id),)
            ).fetchone()
        return _row_to_reading(row) if row else None

    def delete(self, reading_id: UUID) -> bool:
        """Delete a reading by ID. Returns True if found and deleted."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM readings WHERE id = ?", (str(reading_id),)
            )
            return cursor.rowcount > 0

    def count(self) -> int:
        """Return total number of saved readings."""
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]


def _row_to_reading(row: sqlite3.Row) -> Reading:
    """Convert a database row to a Reading object.

    Card names are restored from stored JSON. Full card data (keywords, meanings)
    is not persisted to avoid duplication — those come from card_meanings.yaml.
    """
    try:
        cards_json = json.loads(row["drawn_cards"])
    except (json.JSONDecodeError, KeyError):
        log.warning("Corrupt drawn_cards JSON for reading %s", row["id"])
        cards_json = []

    drawn_cards = []
    for entry in cards_json:
        try:
            card = Card(
                id=entry["card_id"],
                name=entry.get("card_name", ""),
                name_zh=entry.get("card_name_zh", ""),
                arcana=Arcana(entry.get("card_arcana", "major")),
                number=entry.get("card_number", 0),
                element="",
                astrology="",
                keywords_upright=(),
                keywords_reversed=(),
                meaning_upright="",
                meaning_reversed="",
            )
            pos = Position(
                name=entry["position_name"],
                name_zh=entry["position_name_zh"],
                description=entry["position_desc"],
            )
            drawn_cards.append(DrawnCard(card=card, position=pos, is_reversed=entry["is_reversed"]))
        except (KeyError, TypeError, ValueError):
            log.warning("Skipping corrupt card entry in reading %s", row["id"])
            continue

    return Reading(
        id=UUID(row["id"]),
        timestamp=datetime.fromisoformat(row["timestamp"]),
        question=row["question"],
        spread_name=row["spread_name"],
        spread_name_zh=row["spread_name_zh"],
        drawn_cards=drawn_cards,
        interpretation=row["interpretation"],
    )
