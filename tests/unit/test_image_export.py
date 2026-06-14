"""Tests for interpretation image export."""

from PIL import Image, ImageDraw

from nekomata.core.card.data import load_all_cards
from nekomata.core.card.types import DrawnCard, Position
from nekomata.core.render.image_export import (
    _FONT_BODY,
    _FONT_BOLD,
    _FONT_EMOJI,
    _WIDTH,
    _blur_rect,
    _card_image_path,
    _color_for,
    _draw_blocks,
    _draw_runs,
    _ellipsize,
    _find_emoji_font,
    _find_font,
    _font_for,
    _hex_to_rgb,
    _line_h,
    _load_card_image,
    _parse_blocks,
    _parse_inline,
    _Run,
    _split_emoji_runs,
    _text_w,
    _tokenize,
    _wrap_plain,
    _wrap_runs,
    render_interp_image,
    save_image,
)


def _drawn_cards(count: int = 3) -> list[DrawnCard]:
    cards = load_all_cards()[:count]
    return [
        DrawnCard(
            card=card,
            position=Position("Position", "位置", ""),
            is_reversed=index % 2 == 1,
        )
        for index, card in enumerate(cards)
    ]


# -- Low-level helpers --


def test_hex_to_rgb():
    assert _hex_to_rgb("#ff2d8f") == (255, 45, 143)
    assert _hex_to_rgb("aebbc3") == (174, 187, 195)


def test_hex_to_rgb_short():
    r, g, b = _hex_to_rgb("#000000")
    assert (r, g, b) == (0, 0, 0)


def test_split_emoji_runs_strips_emojis():
    runs = _split_emoji_runs("hello 🐱 world", "body")
    texts = [r.text for r in runs]
    # Emoji should be stripped; resulting text should contain no emoji
    assert "hello" in "".join(texts)
    assert "world" in "".join(texts)
    assert "🐱" not in "".join(texts)


def test_split_emoji_runs_preserves_kind():
    runs = _split_emoji_runs("bold text", "bold")
    assert all(r.kind == "bold" for r in runs)


def test_find_font_falls_back_to_default(monkeypatch):
    monkeypatch.setattr("nekomata.core.render.image_export._font_candidates", lambda bold=False: ("/missing.ttf",))
    monkeypatch.setattr("nekomata.core.render.image_export.os.path.exists", lambda path: False)

    assert _find_font(12) is not None


def test_find_emoji_font_missing_or_invalid(monkeypatch):
    monkeypatch.setattr("nekomata.core.render.image_export.os.path.exists", lambda path: False)
    assert _find_emoji_font() is None

    monkeypatch.setattr("nekomata.core.render.image_export.os.path.exists", lambda path: True)
    monkeypatch.setattr(
        "nekomata.core.render.image_export.ImageFont.truetype",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError),
    )
    assert _find_emoji_font() is None


def test_tokenize_ascii():
    tokens = _tokenize("hello world")
    assert "hello" in tokens
    assert " " in tokens
    assert "world" in tokens


def test_tokenize_cjk():
    tokens = _tokenize("你好世界")
    # Each CJK char should be its own token
    assert tokens == ["你", "好", "世", "界"]


def test_tokenize_mixed():
    tokens = _tokenize("说hello吧")
    assert "说" in tokens
    assert "hello" in tokens
    assert "吧" in tokens


def test_parse_inline_plain():
    runs = _parse_inline("just plain text")
    assert len(runs) == 1
    assert runs[0].text == "just plain text"
    assert runs[0].kind == "body"


def test_parse_inline_bold():
    runs = _parse_inline("some **bold** text")
    kinds = [r.kind for r in runs]
    assert "bold" in kinds


def test_parse_inline_code():
    runs = _parse_inline("use `foo` here")
    kinds = [r.kind for r in runs]
    assert "code" in kinds


def test_parse_inline_italic_keeps_default_kind():
    runs = _parse_inline("some *emphasis* text")
    assert [run.text for run in runs] == ["some ", "emphasis", " text"]
    assert all(run.kind == "body" for run in runs)


def test_font_and_color_helpers_cover_known_kinds():
    assert _font_for("bold") is _FONT_BOLD
    assert _font_for("h1") is not _FONT_BODY
    assert _font_for("h2") is not _FONT_BODY
    assert _font_for("h3") is not _FONT_BODY
    assert _font_for("code") is _FONT_BOLD
    assert _font_for("emoji") is (_FONT_EMOJI or _FONT_BODY)

    assert _color_for("bold") == _color_for("body")
    assert _color_for("h1") != _color_for("body")
    assert _color_for("h2") != _color_for("body")
    assert _color_for("h3") != _color_for("body")
    assert _color_for("code") != _color_for("body")


def test_parse_blocks_paragraph():
    blocks = _parse_blocks("Hello world\n\nSecond paragraph", 800)
    assert len(blocks) == 2
    assert blocks[0].kind == "paragraph"
    assert blocks[1].kind == "paragraph"


def test_parse_blocks_heading():
    blocks = _parse_blocks("# Title\n## Sub\n### Subsub", 800)
    assert len(blocks) == 3
    assert all(b.kind == "heading" for b in blocks)


def test_parse_blocks_list():
    blocks = _parse_blocks("- item one\n- item two\n1. numbered", 800)
    assert len(blocks) == 3
    assert all(b.kind == "list" for b in blocks)


def test_parse_blocks_quote():
    blocks = _parse_blocks("> quoted text", 800)
    assert len(blocks) == 1
    assert blocks[0].kind == "quote"


def test_parse_blocks_hr():
    blocks = _parse_blocks("---", 800)
    assert len(blocks) == 1
    assert blocks[0].kind == "hr"


def test_wrap_runs_basic():
    runs = [_Run("hello world foo bar baz", "body")]
    lines = _wrap_runs(runs, 100)
    assert len(lines) >= 1


def test_wrap_runs_with_bullet():
    runs = [_Run("some item text", "body")]
    lines = _wrap_runs(runs, 800, indent=34, bullet="•")
    assert len(lines) >= 1
    assert lines[0].bullet == "•"


def test_wrap_plain_and_ellipsize_long_text():
    lines = _wrap_plain("hello world " * 20, 80, _FONT_BODY)
    assert len(lines) > 1
    assert _ellipsize("short", 1000, _FONT_BODY) == "short"
    assert _ellipsize("very long text " * 20, 40, _FONT_BODY).endswith("...")


def test_text_w():
    w = _text_w("hello", _FONT_BODY)
    assert isinstance(w, int)
    assert w > 0


def test_line_h():
    h = _line_h(_FONT_BODY)
    assert isinstance(h, int)
    assert h > 0


# -- High-level rendering --


def test_render_interp_image_handles_markdown_and_cards():
    md = (
        "你好呀，远方的朋友。**星辰**已经听见了你的声音。\n\n"
        "## 牌面解析\n\n"
        "- 从迷雾中苏醒\n"
        "- 释放与解脱\n\n"
        "> 你现在的状态是安全的。\n\n"
        "1. 直面恐惧\n"
        "2. 信任直觉\n"
    )

    img = render_interp_image(md, _drawn_cards(5))

    assert img.size[0] == _WIDTH
    assert img.size[1] > 700
    assert img.getbbox() is not None


def test_render_interp_image_no_cards():
    img = render_interp_image("Simple text interpretation.")
    assert img.size[0] == _WIDTH
    assert img.size[1] > 100
    assert img.mode == "RGB"


def test_render_interp_image_empty_text():
    img = render_interp_image("")
    assert img.size[0] == _WIDTH
    assert img.mode == "RGB"


def test_render_interp_image_with_question():
    img = render_interp_image(
        "Some interpretation text.",
        _drawn_cards(1),
        question="Will I find love?",
    )
    assert img.size[0] == _WIDTH
    assert img.size[1] > 200


def test_render_interp_image_chinese():
    md = "**愚者**代表新的开始。\n\n> 勇敢地迈出第一步。"
    img = render_interp_image(md, _drawn_cards(3), lang="zh")
    assert img.size[0] == _WIDTH
    assert img.getbbox() is not None


def test_render_interp_image_reversed_card():
    """Verify reversed cards render without error."""
    cards = load_all_cards()[:1]
    drawn = [DrawnCard(card=cards[0], position=Position("Pos", "位置", ""), is_reversed=True)]
    img = render_interp_image("Reversed card test.", drawn)
    assert img.getbbox() is not None


def test_load_card_image_missing_and_reversed(tmp_path):
    dc = _drawn_cards(1)[0]
    assert _card_image_path(dc) == dc.card.image_path

    missing_card = type(dc.card)(
        id=dc.card.id,
        name=dc.card.name,
        name_zh=dc.card.name_zh,
        arcana=dc.card.arcana,
        number=dc.card.number,
        element=dc.card.element,
        astrology=dc.card.astrology,
        keywords_upright=dc.card.keywords_upright,
        keywords_reversed=dc.card.keywords_reversed,
        meaning_upright=dc.card.meaning_upright,
        meaning_reversed=dc.card.meaning_reversed,
        image_path=tmp_path / "missing.png",
        keywords_upright_en=dc.card.keywords_upright_en,
        keywords_reversed_en=dc.card.keywords_reversed_en,
        meaning_upright_en=dc.card.meaning_upright_en,
        meaning_reversed_en=dc.card.meaning_reversed_en,
    )
    assert _load_card_image(DrawnCard(missing_card, dc.position, False)) is None

    img_path = tmp_path / "card.png"
    Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(img_path)
    present_card = type(dc.card)(
        id=dc.card.id,
        name=dc.card.name,
        name_zh=dc.card.name_zh,
        arcana=dc.card.arcana,
        number=dc.card.number,
        element=dc.card.element,
        astrology=dc.card.astrology,
        keywords_upright=dc.card.keywords_upright,
        keywords_reversed=dc.card.keywords_reversed,
        meaning_upright=dc.card.meaning_upright,
        meaning_reversed=dc.card.meaning_reversed,
        image_path=img_path,
        keywords_upright_en=dc.card.keywords_upright_en,
        keywords_reversed_en=dc.card.keywords_reversed_en,
        meaning_upright_en=dc.card.meaning_upright_en,
        meaning_reversed_en=dc.card.meaning_reversed_en,
    )
    loaded = _load_card_image(DrawnCard(present_card, dc.position, True))
    assert loaded is not None
    assert loaded.size[0] > 4


def test_draw_helpers_cover_hr_quote_heading_bullet_and_shadow_bounds():
    img = Image.new("RGBA", (300, 220), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    blocks = _parse_blocks("# Title\n\n- item\n\n> quote\n\n---", 220)

    end_y = _draw_blocks(draw, blocks, 10, 10, 220)
    _draw_runs(draw, 10, end_y, (_Run("inline", "body"),))
    _blur_rect(img, (500, 500, 510, 510), blur_radius=4, rounded_radius=2, fill=(0, 0, 0, 128))

    assert end_y > 10


def test_render_interp_image_many_cards():
    """Test with 7 cards (triggers 2-row layout)."""
    img = render_interp_image("Multi-row test.", _drawn_cards(7))
    assert img.size[0] == _WIDTH
    assert img.size[1] > 400


def test_render_interp_image_rich_markdown():
    md = (
        "# 大标题\n\n"
        "## 中标题\n\n"
        "### 小标题\n\n"
        "正文带**粗体**和`代码`。\n\n"
        "- 列表一\n"
        "- 列表二\n\n"
        "> 引用文本\n\n"
        "---\n\n"
        "尾段。"
    )
    img = render_interp_image(md, _drawn_cards(3))
    assert img.getbbox() is not None


def test_save_image_creates_file(tmp_path):
    img = Image.new("RGB", (100, 100), (128, 128, 128))
    path = save_image(img)
    assert path.endswith(".png")
    assert Image.open(path).size == (100, 100)
    import os

    os.unlink(path)
