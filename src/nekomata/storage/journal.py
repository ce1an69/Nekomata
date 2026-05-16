from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import UUID

from nekomata.card.types import Arcana, Card, DrawnCard, Position, Reading


class Journal:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    def _init_db(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS readings (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                question TEXT NOT NULL,
                spread_name TEXT NOT NULL,
                spread_name_zh TEXT NOT NULL,
                interpretation TEXT,
                cards_json TEXT NOT NULL
            )
        """)

    def save(self, reading: Reading) -> None:
        cards_data = []
        for dc in reading.drawn_cards:
            cards_data.append({
                "card_id": dc.card.id,
                "card_name": dc.card.name,
                "card_name_zh": dc.card.name_zh,
                "card_arcana": dc.card.arcana.value,
                "position_name": dc.position.name,
                "position_name_zh": dc.position.name_zh,
                "position_description": dc.position.description,
                "is_reversed": dc.is_reversed,
                "keywords": list(
                    dc.card.keywords_reversed if dc.is_reversed else dc.card.keywords_upright
                ),
                "meaning": (
                    dc.card.meaning_reversed if dc.is_reversed else dc.card.meaning_upright
                ),
            })
        self._conn.execute(
            "INSERT INTO readings VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(reading.id),
                reading.timestamp.isoformat(),
                reading.question,
                reading.spread_name,
                reading.spread_name_zh,
                reading.interpretation,
                json.dumps(cards_data, ensure_ascii=False),
            ),
        )
        self._conn.commit()

    def load_recent(self, limit: int = 10) -> list[Reading]:
        rows = self._conn.execute(
            "SELECT * FROM readings ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        readings = []
        for row in rows:
            id_str, ts_str, question, spread_name, spread_name_zh, interp, cards_json = row
            cards_data = json.loads(cards_json)
            drawn_cards = []
            for cd in cards_data:
                card = Card(
                    id=cd["card_id"],
                    name=cd["card_name"],
                    name_zh=cd["card_name_zh"],
                    arcana=Arcana(cd["card_arcana"]),
                    number=0,
                    element="",
                    astrology="",
                    keywords_upright=tuple(cd["keywords"]),
                    keywords_reversed=tuple(cd["keywords"]),
                    meaning_upright=cd["meaning"],
                    meaning_reversed=cd["meaning"],
                )
                pos = Position(
                    name=cd["position_name"],
                    name_zh=cd["position_name_zh"],
                    description=cd["position_description"],
                )
                drawn_cards.append(DrawnCard(card=card, position=pos, is_reversed=cd["is_reversed"]))
            readings.append(Reading(
                id=UUID(id_str),
                timestamp=datetime.fromisoformat(ts_str),
                question=question,
                spread_name=spread_name,
                spread_name_zh=spread_name_zh,
                drawn_cards=drawn_cards,
                interpretation=interp,
            ))
        return readings
