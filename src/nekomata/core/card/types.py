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
    keywords_upright_en: tuple[str, ...] = ()
    keywords_reversed_en: tuple[str, ...] = ()
    meaning_upright_en: str = ""
    meaning_reversed_en: str = ""


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
