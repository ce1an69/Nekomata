"""Core data types for tarot cards, positions, and readings."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import UUID, uuid4


class Arcana(str, Enum):
    MAJOR = "major"
    CUPS = "cups"
    WANDS = "wands"
    SWORDS = "swords"
    PENTACLES = "pentacles"


# Chinese display names for each arcana suit
ARCANA_ZH = {
    Arcana.MAJOR: "大阿卡纳",
    Arcana.CUPS: "圣杯",
    Arcana.WANDS: "权杖",
    Arcana.SWORDS: "宝剑",
    Arcana.PENTACLES: "星币",
}


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

    @property
    def status_label(self) -> str:
        """Chinese label for upright/reversed state."""
        return "逆位" if self.is_reversed else "正位"

    @property
    def keywords(self) -> tuple[str, ...]:
        """Keywords based on upright/reversed state."""
        return self.card.keywords_reversed if self.is_reversed else self.card.keywords_upright

    @property
    def meaning(self) -> str:
        """Meaning based on upright/reversed state."""
        return self.card.meaning_reversed if self.is_reversed else self.card.meaning_upright


@dataclass
class Reading:
    """A completed tarot reading session, persisted to the journal."""
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.now)
    question: str = ""
    spread_name: str = ""
    spread_name_zh: str = ""
    drawn_cards: list[DrawnCard] = field(default_factory=list)
    interpretation: str | None = None
