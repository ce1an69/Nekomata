from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import UUID


class Arcana(str, Enum):
    MAJOR = "major"
    CUPS = "cups"
    WANDS = "wands"
    SWORDS = "swords"
    PENTACLES = "pentacles"


@dataclass(frozen=True)
class Card:
    id: str
    name: str
    name_zh: str
    arcana: Arcana
    number: int
    element: str
    astrology: str
    keywords_upright: tuple[str, ...]
    keywords_reversed: tuple[str, ...]
    meaning_upright: str
    meaning_reversed: str
    image_path: Path | None = None


@dataclass(frozen=True)
class Position:
    name: str
    name_zh: str
    description: str


@dataclass
class DrawnCard:
    card: Card
    position: Position
    is_reversed: bool


@dataclass
class Reading:
    id: UUID
    timestamp: datetime
    question: str
    spread_name: str
    spread_name_zh: str
    drawn_cards: list[DrawnCard]
    interpretation: str | None = None
