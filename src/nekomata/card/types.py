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


# Display names for each arcana suit (locale-aware)
def arcana_display(arcana: Arcana) -> str:
    from nekomata.i18n import arcana_label
    return arcana_label(arcana.value)


# Legacy mapping — still used by server.py _card_to_dict
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
    keywords_upright_en: tuple[str, ...] = ()
    keywords_reversed_en: tuple[str, ...] = ()
    meaning_upright_en: str = ""
    meaning_reversed_en: str = ""

    @property
    def display_name(self) -> str:
        """Locale-aware card name."""
        from nekomata.i18n import get_lang
        return self.name if get_lang() == "en" else self.name_zh

    def keywords_for(self, reversed: bool) -> tuple[str, ...]:
        """Keywords for a given orientation, locale-aware."""
        from nekomata.i18n import get_lang
        if get_lang() == "en":
            en = self.keywords_reversed_en if reversed else self.keywords_upright_en
            if en:
                return en
        return self.keywords_reversed if reversed else self.keywords_upright

    def meaning_for(self, reversed: bool) -> str:
        """Meaning for a given orientation, locale-aware."""
        from nekomata.i18n import get_lang
        if get_lang() == "en":
            en = self.meaning_reversed_en if reversed else self.meaning_upright_en
            if en:
                return en
        return self.meaning_reversed if reversed else self.meaning_upright


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
        """Label for upright/reversed state, locale-aware."""
        from nekomata.i18n import get_lang, ui_section
        if get_lang() != "en":
            cd = ui_section("card_detail")
            return cd.get("status_reversed" if self.is_reversed else "status_upright",
                          "reversed" if self.is_reversed else "upright")
        return "reversed" if self.is_reversed else "upright"

    @property
    def keywords(self) -> tuple[str, ...]:
        """Keywords based on upright/reversed state, locale-aware."""
        return self.card.keywords_for(self.is_reversed)

    @property
    def meaning(self) -> str:
        """Meaning based on upright/reversed state, locale-aware."""
        return self.card.meaning_for(self.is_reversed)
