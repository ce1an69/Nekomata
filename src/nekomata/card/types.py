"""Core data types for tarot cards, positions, and readings."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Arcana(str, Enum):
    MAJOR = "major"
    CUPS = "cups"
    WANDS = "wands"
    SWORDS = "swords"
    PENTACLES = "pentacles"


# Display names for each arcana suit
ARCANA_ZH = {
    Arcana.MAJOR: "大阿卡纳",
    Arcana.CUPS: "圣杯",
    Arcana.WANDS: "权杖",
    Arcana.SWORDS: "宝剑",
    Arcana.PENTACLES: "星币",
}

# Roman numerals for Major Arcana display
ROMAN = [
    "0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI",
]


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
        """Label for upright/reversed state."""
        return "reversed" if self.is_reversed else "upright"

    @property
    def keywords(self) -> tuple[str, ...]:
        """Keywords based on upright/reversed state."""
        return self.card.keywords_reversed if self.is_reversed else self.card.keywords_upright

    @property
    def meaning(self) -> str:
        """Meaning based on upright/reversed state."""
        return self.card.meaning_reversed if self.is_reversed else self.card.meaning_upright
