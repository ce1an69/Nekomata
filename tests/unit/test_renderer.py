from pathlib import Path

from rich.panel import Panel

from nekomata.card.types import Arcana, Card, DrawnCard, Position
from nekomata.render.card_renderer import (
    render_card_text,
    render_card_detail,
    get_preview_path,
    render_card_image,
    render_card_image_detail,
    _load_card_image,
    _load_card_detail_image,
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
    s = str(render_card_text(make_drawn(reversed=True)).renderable)
    assert "↕" in s
    assert "reversed" in s


def test_render_card_text_upright():
    s = str(render_card_text(make_drawn()).renderable)
    assert "upright" in s


def test_render_card_text_position_in_title():
    assert "Daily" in str(render_card_text(make_drawn()).title)


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
    assert "reversed" in s
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


def test_render_card_image_no_image():
    """Cards without image_path should return None."""
    dc = make_drawn()
    assert dc.card.image_path is None
    assert render_card_image(dc) is None


def test_render_card_image_with_png():
    """Cards with a real PNG should return a Panel."""
    card = Card(
        id="major_02", name="The High Priestess", name_zh="女祭司",
        arcana=Arcana.MAJOR, number=2, element="water", astrology="Moon",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_02.png"),
    )
    pos = Position(name="Test", name_zh="测试", description="test")
    dc = DrawnCard(card=card, position=pos, is_reversed=False)
    result = render_card_image(dc, size="compact")
    assert isinstance(result, Panel)


def test_render_card_image_reversed():
    """Reversed card image should still render."""
    card = Card(
        id="major_02", name="The High Priestess", name_zh="女祭司",
        arcana=Arcana.MAJOR, number=2, element="water", astrology="Moon",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_02.png"),
    )
    pos = Position(name="Test", name_zh="测试", description="test")
    dc = DrawnCard(card=card, position=pos, is_reversed=True)
    result = render_card_image(dc, size="compact")
    assert isinstance(result, Panel)
    assert "↕" in str(result.title)


def test_load_card_image_resizes():
    """_load_card_image should resize to the requested size."""
    card = Card(
        id="major_02", name="The High Priestess", name_zh="女祭司",
        arcana=Arcana.MAJOR, number=2, element="water", astrology="Moon",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_02.png"),
    )
    img = _load_card_image(card, size="compact")
    assert img is not None
    assert img.size == (32, 48)


def test_load_card_image_reversed_rotates():
    """Reversed card should have rotated image."""
    card = Card(
        id="major_02", name="The High Priestess", name_zh="女祭司",
        arcana=Arcana.MAJOR, number=2, element="water", astrology="Moon",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_02.png"),
    )
    img_normal = _load_card_image(card, size="full", upside_down=False)
    img_reversed = _load_card_image(card, size="full", upside_down=True)
    assert img_normal.tobytes() != img_reversed.tobytes()


def test_render_card_image_detail_with_png():
    """Detail preview should render with 128x192 PNG."""
    card = Card(
        id="major_02", name="The High Priestess", name_zh="女祭司",
        arcana=Arcana.MAJOR, number=2, element="water", astrology="Moon",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_02.png"),
    )
    pos = Position(name="Test", name_zh="测试", description="test")
    dc = DrawnCard(card=card, position=pos, is_reversed=False)
    result = render_card_image_detail(dc)
    assert isinstance(result, Panel)


def test_load_card_detail_image_resizes_to_preview_size():
    """Detail preview should be resized before rich-pixels renders it."""
    card = Card(
        id="major_02", name="The High Priestess", name_zh="女祭司",
        arcana=Arcana.MAJOR, number=2, element="water", astrology="Moon",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_02.png"),
    )
    img = _load_card_detail_image(card)
    assert img is not None
    assert img.size == (56, 84)


def test_render_card_image_detail_no_image():
    """Cards without preview PNG should return None."""
    dc = make_drawn()
    assert render_card_image_detail(dc) is None


def test_render_card_image_detail_reversed():
    """Detail preview of a reversed card shows 'reversed' in title."""
    card = Card(
        id="major_02", name="The High Priestess", name_zh="女祭司",
        arcana=Arcana.MAJOR, number=2, element="water", astrology="Moon",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_02.png"),
    )
    pos = Position(name="Test", name_zh="测试", description="test")
    dc_upright = DrawnCard(card=card, position=pos, is_reversed=False)
    dc_reversed = DrawnCard(card=card, position=pos, is_reversed=True)

    result_up = render_card_image_detail(dc_upright)
    result_rev = render_card_image_detail(dc_reversed)

    assert isinstance(result_up, Panel)
    assert isinstance(result_rev, Panel)
    assert "reversed" in result_rev.title
