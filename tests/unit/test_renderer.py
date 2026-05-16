from pathlib import Path

from rich.panel import Panel

from nekomata.card.types import Arcana, Card, DrawnCard, Position
from nekomata.render.card_renderer import (
    render_card_text,
    render_card_detail,
    render_reading_summary,
    get_preview_path,
)


def make_drawn(reversed: bool = False) -> DrawnCard:
    card = Card(
        id="major_00", name="The Fool", name_zh="愚者",
        arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
        keywords_upright=("新开始", "天真", "冒险"),
        keywords_reversed=("鲁莽", "冒失", "停滞"),
        meaning_upright="一段新旅程的开始。",
        meaning_reversed="过于鲁莽。",
    )
    pos = Position(name="Daily", name_zh="今日指引", description="今日灵感")
    return DrawnCard(card=card, position=pos, is_reversed=reversed)


def test_render_card_text_returns_panel():
    assert isinstance(render_card_text(make_drawn()), Panel)


def test_render_card_text_contains_name():
    s = str(render_card_text(make_drawn()).renderable)
    assert "愚者" in s
    assert "The Fool" in s


def test_render_card_text_reversed():
    assert "逆位" in str(render_card_text(make_drawn(reversed=True)).renderable)


def test_render_card_text_upright():
    assert "正位" in str(render_card_text(make_drawn()).renderable)


def test_render_card_text_position_in_title():
    assert "今日指引" in str(render_card_text(make_drawn()).title)


def test_render_reading_summary():
    cards = [make_drawn(False), make_drawn(True)]
    assert isinstance(render_reading_summary(cards, "今天运势如何？"), Panel)


def test_render_card_detail_returns_panel():
    assert isinstance(render_card_detail(make_drawn()), Panel)


def test_render_card_detail_shows_full_info():
    s = str(render_card_detail(make_drawn()).renderable)
    assert "愚者" in s
    assert "air" in s
    assert "Uranus" in s
    assert "新开始" in s
    assert "鲁莽" in s
    assert "一段新旅程的开始" in s


def test_render_card_detail_reversed():
    s = str(render_card_detail(make_drawn(reversed=True)).renderable)
    assert "逆位" in s
    assert "过于鲁莽" in s


def test_get_preview_path():
    card = Card(
        id="major_00", name="The Fool", name_zh="愚者",
        arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_00.png"),
    )
    assert get_preview_path(card) == Path("assets/cards/major/major_00_detail.png")


def test_get_preview_path_no_image():
    card = Card(
        id="major_00", name="The Fool", name_zh="愚者",
        arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
    )
    assert get_preview_path(card) is None
