"""Locale-aware display helpers for Card and DrawnCard.

Pure functions with an explicit ``lang`` parameter — no global i18n state.
"""

from nekomata.card.types import Card


def card_name(card: Card, lang: str) -> str:
    return card.name if lang == "en" else card.name_zh


def card_keywords(card: Card, reversed: bool, lang: str) -> tuple[str, ...]:
    if lang == "en":
        en = card.keywords_reversed_en if reversed else card.keywords_upright_en
        if en:
            return en
    return card.keywords_reversed if reversed else card.keywords_upright


def card_meaning(card: Card, reversed: bool, lang: str) -> str:
    if lang == "en":
        en = card.meaning_reversed_en if reversed else card.meaning_upright_en
        if en:
            return en
    return card.meaning_reversed if reversed else card.meaning_upright


def status_label(is_reversed: bool, lang: str) -> str:
    if lang != "en":
        from nekomata.i18n import ui_section

        cd = ui_section("card_detail", lang)
        return cd.get(
            "status_reversed" if is_reversed else "status_upright",
            "reversed" if is_reversed else "upright",
        )
    return "reversed" if is_reversed else "upright"
