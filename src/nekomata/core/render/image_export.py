"""Render markdown interpretation text to a styled PNG image using Pillow."""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from glob import glob
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from nekomata._paths import assets_dir
from nekomata.card.display import card_name as _card_name, status_label as _status_label
from nekomata.render.card_renderer import get_origin_path, get_preview_path
from nekomata.render.styles import (
    C_LAVENDER,
    C_MANTLE,
    C_MAUVE,
    C_SUBTEXT0,
    C_SUBTEXT1,
    C_SURFACE2,
    C_TEXT,
)

if TYPE_CHECKING:
    from nekomata.card.types import DrawnCard


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


_WIDTH = 1080
_CARD_W = 160
_CARD_H = 240
_LINE_GAP = 7
_PARA_GAP = 10
_SECTION_GAP = 24
_WINDOW_MARGIN_X = 78
_WINDOW_MARGIN_Y = 78
_WINDOW_PAD_X = 56
_WINDOW_PAD_BOTTOM = 46
_WINDOW_CHROME_H = 96

_BG = _hex_to_rgb("#aebbc3")
_WINDOW = _hex_to_rgb(C_MANTLE)
_TEXT = _hex_to_rgb(C_TEXT)
_MAUVE = _hex_to_rgb(C_MAUVE)
_LAVENDER = _hex_to_rgb(C_LAVENDER)
_PINK = _hex_to_rgb("#ff2d8f")
_CYAN = _hex_to_rgb("#89dceb")
_SUBTEXT = _hex_to_rgb(C_SUBTEXT1)
_MUTED = _hex_to_rgb(C_SUBTEXT0)
_RULE = _hex_to_rgb(C_SURFACE2)
_DOT_RED = _hex_to_rgb("#ff5f57")
_DOT_YELLOW = _hex_to_rgb("#febc2e")
_DOT_GREEN = _hex_to_rgb("#28c840")


@dataclass(frozen=True)
class _Run:
    text: str
    kind: str = "body"


@dataclass(frozen=True)
class _Line:
    runs: tuple[_Run, ...]
    indent: int = 0
    bullet: str = ""


@dataclass(frozen=True)
class _Block:
    kind: str
    lines: tuple[_Line, ...] = ()


def _bundled_font_path(*, bold: bool = False) -> str:
    name = (
        "MapleMonoNormal-NF-CN-Bold.ttf"
        if bold
        else "MapleMonoNormal-NF-CN-Regular.ttf"
    )
    return str(assets_dir() / "fonts" / name)


def _font_candidates(*, bold: bool = False) -> tuple[str, ...]:
    pingfang_assets = tuple(sorted(glob("/System/Library/AssetsV2/com_apple_MobileAsset_Font8/*/AssetData/PingFang.ttc")))
    return (_bundled_font_path(bold=bold),) + pingfang_assets + (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )


def _find_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _font_candidates(bold=bold):
        if not os.path.exists(path):
            continue
        if path.endswith(".ttf") or path.endswith(".otf"):
            indexes = (0,)
        elif path.endswith("PingFang.ttc"):
            indexes = (7, 3, 11, 0, 1, 2) if bold else (3, 0, 1, 2, 7)
        else:
            indexes = (1, 0) if bold else (0, 1)
        for index in indexes:
            try:
                return ImageFont.truetype(path, size, index=index)
            except Exception:
                continue
    return ImageFont.load_default(size)


def _find_emoji_font(size: int = 32) -> ImageFont.FreeTypeFont | None:
    path = "/System/Library/Fonts/Apple Color Emoji.ttc"
    if not os.path.exists(path):
        return None
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return None


_FONT_BODY = _find_font(23)
_FONT_BOLD = _find_font(23, bold=True)
_FONT_H1 = _find_font(31, bold=True)
_FONT_H2 = _find_font(28, bold=True)
_FONT_H3 = _find_font(25, bold=True)
_FONT_SMALL = _find_font(18)
_FONT_LABEL = _find_font(20, bold=True)
_FONT_FOOTER = _find_font(18)
_FONT_QUESTION = _find_font(29, bold=True)
_FONT_EMOJI = _find_emoji_font()



def _font_for(kind: str):
    if kind == "bold":
        return _FONT_BOLD
    if kind == "h1":
        return _FONT_H1
    if kind == "h2":
        return _FONT_H2
    if kind == "h3":
        return _FONT_H3
    if kind == "code":
        return _FONT_BOLD
    if kind == "emoji" and _FONT_EMOJI is not None:
        return _FONT_EMOJI
    return _FONT_BODY


def _color_for(kind: str):
    if kind == "bold":
        return _TEXT
    if kind == "h1":
        return _MAUVE
    if kind == "h2":
        return _PINK
    if kind == "h3":
        return _LAVENDER
    if kind == "code":
        return _LAVENDER
    return _TEXT


def _is_emoji_char(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x1F000 <= cp <= 0x1FAFF
        or 0x2600 <= cp <= 0x27BF
        or cp in {0xFE0F, 0x200D}
    )


def _split_emoji_runs(text: str, kind: str) -> list[_Run]:
    runs: list[_Run] = []
    buf = ""

    def flush_text() -> None:
        nonlocal buf
        if buf:
            runs.append(_Run(buf, kind))
            buf = ""

    for ch in text:
        if _is_emoji_char(ch):
            if ch in {chr(0xFE0F), chr(0x200D)}:
                continue
            # Strip all detected emojis — Pillow cannot render them.
            # Add a space to avoid merging adjacent text runs.
            if buf and not buf.endswith(" "):
                buf += " "
        else:
            buf += ch
    flush_text()
    return runs


def _text_w(text: str, font) -> int:
    if not text:
        return 0
    left, _, right, _ = font.getbbox(text)
    return right - left


def _line_h(font) -> int:
    _, top, _, bottom = font.getbbox("星猫Ag")
    return bottom - top + _LINE_GAP


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    buf = ""
    for ch in text:
        if ch.isspace():
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(ch)
        elif "\u4e00" <= ch <= "\u9fff" or ch in "，。？！、；：《》（）“”‘’":
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(ch)
        else:
            buf += ch
    if buf:
        tokens.append(buf)
    return tokens


def _parse_inline(text: str, default_kind: str = "body") -> list[_Run]:
    runs: list[_Run] = []
    pattern = re.compile(r"(\*\*.+?\*\*|`.+?`|\*.+?\*)")
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            runs.extend(_split_emoji_runs(text[pos:match.start()], default_kind))
        token = match.group(0)
        if token.startswith("**"):
            kind = default_kind if default_kind.startswith("h") else "bold"
            runs.extend(_split_emoji_runs(token[2:-2], kind))
        elif token.startswith("`"):
            runs.extend(_split_emoji_runs(token[1:-1], "code"))
        else:
            runs.extend(_split_emoji_runs(token[1:-1], default_kind))
        pos = match.end()
    if pos < len(text):
        runs.extend(_split_emoji_runs(text[pos:], default_kind))
    return [run for run in runs if run.text]


def _wrap_runs(runs: list[_Run], max_w: int, *, indent: int = 0, bullet: str = "") -> tuple[_Line, ...]:
    lines: list[_Line] = []
    current: list[_Run] = []
    current_w = 0
    available = max(80, max_w - indent)

    for run in runs:
        font = _font_for(run.kind)
        for token in _tokenize(run.text):
            token_w = _text_w(token, font)
            if current and current_w + token_w > available:
                lines.append(_Line(tuple(current), indent=indent, bullet=bullet if not lines else ""))
                current = []
                current_w = 0
            if token.isspace() and not current:
                continue
            current.append(_Run(token, run.kind))
            current_w += token_w

    if current:
        lines.append(_Line(tuple(current), indent=indent, bullet=bullet if not lines else ""))
    return tuple(lines)


def _parse_blocks(md_text: str, max_w: int) -> list[_Block]:
    blocks: list[_Block] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph:
            return
        text = " ".join(paragraph)
        blocks.append(_Block("paragraph", _wrap_runs(_parse_inline(text), max_w)))
        paragraph.clear()

    for raw_line in md_text.replace("\r\n", "\n").split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            continue
        if stripped in {"---", "***", "___"}:
            flush_paragraph()
            blocks.append(_Block("hr"))
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            blocks.append(_Block("heading", _wrap_runs(_parse_inline(stripped[4:], "h3"), max_w)))
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            blocks.append(_Block("heading", _wrap_runs(_parse_inline(stripped[3:], "h2"), max_w)))
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            blocks.append(_Block("heading", _wrap_runs(_parse_inline(stripped[2:], "h1"), max_w)))
            continue
        if stripped.startswith("> "):
            flush_paragraph()
            blocks.append(_Block("quote", _wrap_runs(_parse_inline(stripped[2:]), max_w, indent=28)))
            continue
        list_match = re.match(r"^([-*]|\d+\.)\s+(.+)$", stripped)
        if list_match:
            flush_paragraph()
            marker, content = list_match.groups()
            bullet = marker if marker.endswith(".") else "•"
            blocks.append(_Block("list", _wrap_runs(_parse_inline(content), max_w, indent=34, bullet=bullet)))
            continue
        paragraph.append(stripped)

    flush_paragraph()
    return blocks


def _measure_blocks(blocks: list[_Block]) -> int:
    height = 0
    for block in blocks:
        if block.kind == "hr":
            height += _line_h(_FONT_BODY) + _SECTION_GAP
            continue
        line_height = _line_h(_FONT_BODY)
        if block.kind == "heading" and block.lines:
            first_kind = block.lines[0].runs[0].kind
            line_height = _line_h(_font_for(first_kind))
            height += 8
        elif block.kind == "quote":
            height += 10
        height += max(1, len(block.lines)) * line_height
        height += _PARA_GAP if block.kind in {"paragraph", "list", "quote"} else _SECTION_GAP
    return height


def _draw_runs(draw: ImageDraw.ImageDraw, x: int, y: int, runs: tuple[_Run, ...]) -> None:
    cx = x
    for run in runs:
        font = _font_for(run.kind)
        if run.kind == "emoji" and _FONT_EMOJI is not None:
            draw.text((cx, y - 4), run.text, font=font, embedded_color=True)
        else:
            draw.text((cx, y), run.text, fill=_color_for(run.kind), font=font)
        cx += _text_w(run.text, font)


def _draw_blocks(draw: ImageDraw.ImageDraw, blocks: list[_Block], x: int, y: int, max_w: int) -> int:
    for block in blocks:
        if block.kind == "hr":
            dash = "-"
            dash_w = _text_w(dash, _FONT_BOLD)
            count = max(1, max_w // max(1, dash_w))
            draw.text((x, y), dash * count, fill=_MUTED, font=_FONT_BOLD)
            y += _line_h(_FONT_BOLD) + _SECTION_GAP
            continue

        if block.kind == "quote":
            block_h = len(block.lines) * _line_h(_FONT_BODY)
            draw.line([(x + 2, y + 3), (x + 2, y + block_h - 3)], fill=_PINK, width=4)

        if block.kind == "heading":
            y += 8

        for line in block.lines:
            line_kind = line.runs[0].kind if line.runs else "body"
            line_font = _font_for(line_kind)
            if line.bullet:
                draw.text((x + 2, y), line.bullet, fill=_CYAN, font=_FONT_BOLD)
            _draw_runs(draw, x + line.indent, y, line.runs)
            y += _line_h(line_font)

        if block.kind == "quote":
            y += 6
        y += _PARA_GAP if block.kind in {"paragraph", "list", "quote"} else _SECTION_GAP
    return y


def _card_image_path(drawn: DrawnCard):
    return get_preview_path(drawn.card) or get_origin_path(drawn.card) or drawn.card.image_path


def _load_card_image(drawn: DrawnCard) -> Image.Image | None:
    path = _card_image_path(drawn)
    if path is None or not path.exists():
        return None
    with Image.open(path) as source:
        img = source.convert("RGBA")
    if drawn.is_reversed:
        img = img.rotate(180)
    img = img.resize((_CARD_W, _CARD_H), Image.Resampling.NEAREST)
    return img


def _wrap_plain(text: str, max_w: int, font) -> list[str]:
    lines: list[str] = []
    current = ""
    for token in _tokenize(text):
        if not current and token.isspace():
            continue
        candidate = current + token
        if current and _text_w(candidate, font) > max_w:
            lines.append(current.rstrip())
            current = "" if token.isspace() else token
        else:
            current = candidate
    if current:
        lines.append(current.rstrip())
    return lines or [""]


def _ellipsize(text: str, max_w: int, font) -> str:
    if _text_w(text, font) <= max_w:
        return text
    ellipsis = "..."
    available = max(0, max_w - _text_w(ellipsis, font))
    result = ""
    for token in _tokenize(text):
        if _text_w(result + token, font) > available:
            break
        result += token
    return result.rstrip() + ellipsis if result else ellipsis


def _draw_cards(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    drawn_cards: list[DrawnCard],
    y: int,
    *,
    area_x: int,
    area_w: int,
    lang: str = "en",
) -> int:
    if not drawn_cards:
        return y

    rows = 1 if len(drawn_cards) <= 5 else 2
    per_row = (len(drawn_cards) + rows - 1) // rows
    gap = 22
    label_h = 62

    for row in range(rows):
        row_cards = drawn_cards[row * per_row:(row + 1) * per_row]
        row_w = len(row_cards) * _CARD_W + max(0, len(row_cards) - 1) * gap
        x = area_x + (area_w - row_w) // 2
        for drawn in row_cards:
            card = _load_card_image(drawn)
            shadow = (x + 4, y + 4, x + _CARD_W + 4, y + _CARD_H + 4)
            draw.rounded_rectangle(shadow, radius=8, fill=(10, 10, 18))
            draw.rounded_rectangle(
                (x - 4, y - 4, x + _CARD_W + 4, y + _CARD_H + 4),
                radius=8,
                fill=_WINDOW,
                outline=_LAVENDER,
                width=2,
            )
            if card is not None:
                img.alpha_composite(card, (x, y))
            name = _card_name(drawn.card, lang)
            status = _status_label(drawn.is_reversed, lang)
            label = f"{name} · {status}"
            label_y = y + _CARD_H + 8
            for line in _wrap_plain(label, _CARD_W + 18, _FONT_SMALL)[:2]:
                label_w = _text_w(line, _FONT_SMALL)
                draw.text((x + (_CARD_W - label_w) // 2, label_y), line, fill=_SUBTEXT, font=_FONT_SMALL)
                label_y += _line_h(_FONT_SMALL) - 4
            x += _CARD_W + gap
        y += _CARD_H + label_h + 18
    return y + 8


def _blur_rect(
    img: Image.Image,
    shape_rect: tuple[int, int, int, int],
    blur_radius: int,
    fill: tuple[int, int, int, int],
    rounded_radius: int = 0,
) -> None:
    """Draw a rounded rect on a padded crop, blur it, and composite onto img."""
    sx1, sy1, sx2, sy2 = shape_rect
    pad = blur_radius * 3  # enough padding for the Gaussian tail
    # Clamp to image bounds
    cx1 = max(0, sx1 - pad)
    cy1 = max(0, sy1 - pad)
    cx2 = min(img.width, sx2 + pad)
    cy2 = min(img.height, sy2 + pad)
    crop_w, crop_h = cx2 - cx1, cy2 - cy1
    if crop_w <= 0 or crop_h <= 0:
        return
    layer = Image.new("RGBA", (crop_w, crop_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    local_rect = (sx1 - cx1, sy1 - cy1, sx2 - cx1, sy2 - cy1)
    draw.rounded_rectangle(local_rect, radius=rounded_radius, fill=fill)
    layer = layer.filter(ImageFilter.GaussianBlur(blur_radius))
    img.alpha_composite(layer, dest=(cx1, cy1))


def _draw_window_shadow(
    img: Image.Image,
    rect: tuple[int, int, int, int],
    radius: int,
) -> None:
    x1, y1, x2, y2 = rect
    _blur_rect(
        img, (x1, y1 + 18, x2, y2 + 18),
        blur_radius=28, fill=(18, 22, 25, 86), rounded_radius=radius,
    )
    _blur_rect(
        img, (x1 + 18, y2 - 6, x2 - 18, y2 + 22),
        blur_radius=14, fill=(18, 22, 25, 44), rounded_radius=18,
    )


def _draw_window_chrome(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    question: str,
) -> None:
    dot_y = y + 36
    for index, color in enumerate((_DOT_RED, _DOT_YELLOW, _DOT_GREEN)):
        dot_x = x + 50 + index * 40
        draw.ellipse((dot_x - 12, dot_y - 12, dot_x + 12, dot_y + 12), fill=color)

    title = _ellipsize(question, w - 300, _FONT_QUESTION) if question else ""
    title_w = _text_w(title, _FONT_QUESTION)
    if title:
        draw.text((x + (w - title_w) // 2, y + 24), title, fill=_MAUVE, font=_FONT_QUESTION)


def render_interp_image(
    md_text: str,
    drawn_cards: list[DrawnCard] | None = None,
    lang: str = "en",
    question: str = "",
) -> Image.Image:
    """Render a tarot interpretation as a Catppuccin-themed PNG image."""
    window_x = _WINDOW_MARGIN_X
    window_w = _WIDTH - _WINDOW_MARGIN_X * 2
    content_x = window_x + _WINDOW_PAD_X
    content_w = window_w - _WINDOW_PAD_X * 2
    blocks = _parse_blocks(md_text, content_w)

    card_h = 0
    if drawn_cards:
        rows = 1 if len(drawn_cards) <= 5 else 2
        card_h = rows * (_CARD_H + 62 + 18) + 8 + 38

    body_h = _measure_blocks(blocks)
    window_h = _WINDOW_CHROME_H + card_h + body_h + _WINDOW_PAD_BOTTOM + 54
    total_h = max(540, _WINDOW_MARGIN_Y * 2 + window_h)

    img = Image.new("RGBA", (_WIDTH, total_h), _BG + (255,))
    draw = ImageDraw.Draw(img)

    window_y = _WINDOW_MARGIN_Y
    window_rect = (window_x, window_y, window_x + window_w, window_y + window_h)
    _draw_window_shadow(img, window_rect, 10)
    draw.rounded_rectangle(window_rect, radius=10, fill=_WINDOW)
    _draw_window_chrome(draw, window_x, window_y, window_w, question.strip())

    y = window_y + _WINDOW_CHROME_H + 8
    y = _draw_cards(
        draw,
        img,
        drawn_cards or [],
        y,
        area_x=content_x,
        area_w=content_w,
        lang=lang,
    )
    if drawn_cards:
        y += 14
        draw.line([(content_x, y), (content_x + content_w, y)], fill=_RULE, width=1)
        y += 24

    y = _draw_blocks(draw, blocks, content_x, y, content_w)

    footer = "Generated by Nekomata"
    footer_w = _text_w(footer, _FONT_FOOTER)
    draw.text(
        (window_x + window_w - _WINDOW_PAD_X - footer_w, window_y + window_h - 34),
        footer,
        fill=_MUTED,
        font=_FONT_FOOTER,
    )
    return img.convert("RGB")


def save_image(img: Image.Image) -> str:
    """Save image to a temp file and return the path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp, "PNG")
    tmp.close()
    return tmp.name
