from pathlib import Path

from rich.panel import Panel

from nekomata.card.types import Arcana, Card, DrawnCard, Position
from nekomata.render.card_renderer import (
    render_card_text,
    render_card_detail,
    get_preview_path,
    get_origin_path,
    create_card_face_widget,
    create_card_origin_widget,
    _load_image,
    preload_card_image,
    get_cached_image,
    clear_cache,
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


def test_get_origin_path():
    card = Card(
        id="major_00", name="The Fool", name_zh="愚者",
        arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_00.png"),
    )
    assert get_origin_path(card) == Path("assets/cards/major/major_00_origin.png")


def test_create_card_face_widget_no_image():
    """Cards without image_path should return None."""
    dc = make_drawn()
    assert dc.card.image_path is None
    assert create_card_face_widget(dc) is None


def test_create_card_face_widget_with_png():
    """Cards with a real PNG should return an Image widget."""
    card = Card(
        id="major_02", name="The High Priestess", name_zh="女祭司",
        arcana=Arcana.MAJOR, number=2, element="water", astrology="Moon",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_02.png"),
    )
    pos = Position(name="Test", name_zh="测试", description="test")
    dc = DrawnCard(card=card, position=pos, is_reversed=False)
    result = create_card_face_widget(dc)
    assert result is not None
    assert result.has_class("card-face")


def test_load_image_reversed_rotates():
    """Reversed card should have rotated image."""
    card = Card(
        id="major_02", name="The High Priestess", name_zh="女祭司",
        arcana=Arcana.MAJOR, number=2, element="water", astrology="Moon",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_02.png"),
    )
    origin_path = get_origin_path(card)
    img_normal = _load_image(origin_path, upside_down=False)
    img_reversed = _load_image(origin_path, upside_down=True)
    assert img_normal is not None
    assert img_reversed is not None
    assert img_normal.tobytes() != img_reversed.tobytes()


def test_load_image_applies_size_cap():
    """_load_image should cap dimensions."""
    card = Card(
        id="major_02", name="The High Priestess", name_zh="女祭司",
        arcana=Arcana.MAJOR, number=2, element="water", astrology="Moon",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_02.png"),
    )
    img = _load_image(get_origin_path(card))
    assert img is not None
    assert img.size[0] <= 1024
    assert img.size[1] <= 1536


def test_create_card_origin_widget_no_image():
    """Cards without origin PNG should return None."""
    dc = make_drawn()
    assert create_card_origin_widget(dc) is None


def test_create_card_origin_widget_with_png():
    """Cards with a real PNG should return an Image widget."""
    card = Card(
        id="major_02", name="The High Priestess", name_zh="女祭司",
        arcana=Arcana.MAJOR, number=2, element="water", astrology="Moon",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_02.png"),
    )
    pos = Position(name="Test", name_zh="测试", description="test")
    dc = DrawnCard(card=card, position=pos, is_reversed=False)
    result = create_card_origin_widget(dc)
    assert result is not None
    assert result.has_class("card-origin")


def test_preload_and_cache():
    """preload_card_image should populate the cache."""
    clear_cache()
    card = Card(
        id="major_02", name="The High Priestess", name_zh="女祭司",
        arcana=Arcana.MAJOR, number=2, element="water", astrology="Moon",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
        image_path=Path("assets/cards/major/major_02.png"),
    )
    assert get_cached_image(card, is_reversed=False) is None
    preload_card_image(card, is_reversed=False)
    cached = get_cached_image(card, is_reversed=False)
    assert cached is not None
    assert cached.size[0] <= 256
    assert cached.size[1] <= 384
    clear_cache()
