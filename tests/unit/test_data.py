from pathlib import Path

from nekomata.card.data import load_all_cards
from nekomata.card.types import Arcana


DATA_PATH = Path(__file__).parent.parent.parent / "data" / "card_meanings.yaml"


def test_load_returns_78_cards():
    cards = load_all_cards(DATA_PATH)
    assert len(cards) == 78


def test_all_cards_have_required_fields():
    cards = load_all_cards(DATA_PATH)
    for card in cards:
        assert card.id
        assert card.name
        assert card.name_zh
        assert card.arcana in Arcana
        assert card.number >= 0
        assert card.element
        assert card.astrology
        assert len(card.keywords_upright) > 0
        assert len(card.keywords_reversed) > 0
        assert card.meaning_upright
        assert card.meaning_reversed


def test_major_arcana_count():
    cards = load_all_cards(DATA_PATH)
    major = [c for c in cards if c.arcana == Arcana.MAJOR]
    assert len(major) == 22


def test_minor_arcana_count():
    cards = load_all_cards(DATA_PATH)
    for suit in [Arcana.CUPS, Arcana.WANDS, Arcana.SWORDS, Arcana.PENTACLES]:
        suit_cards = [c for c in cards if c.arcana == suit]
        assert len(suit_cards) == 14, f"{suit} should have 14 cards, got {len(suit_cards)}"


def test_no_duplicate_ids():
    cards = load_all_cards(DATA_PATH)
    ids = [c.id for c in cards]
    assert len(ids) == len(set(ids))


def test_major_arcana_numbering():
    cards = load_all_cards(DATA_PATH)
    major = sorted([c for c in cards if c.arcana == Arcana.MAJOR], key=lambda c: c.number)
    assert [c.number for c in major] == list(range(22))
