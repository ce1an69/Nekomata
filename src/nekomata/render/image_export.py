"""Render markdown interpretation text to a styled PNG image using Pillow."""

import logging
import os
import tempfile
import textwrap

from PIL import Image, ImageDraw, ImageFont

from nekomata.render.styles import (
    C_CRUST, C_GOLD, C_LAVENDER, C_MAUVE, C_SUBTEXT0, C_TEXT,
)

log = logging.getLogger(__name__)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


_WIDTH = 720
_PADDING = 36
_LINE_SPACING = 4
_HEADING_SPACING = 16

# Catppuccin Mocha hex → RGB tuples
_BG = _hex_to_rgb(C_CRUST)
_TEXT = _hex_to_rgb(C_TEXT)
_GOLD = _hex_to_rgb(C_GOLD)
_MAUVE = _hex_to_rgb(C_MAUVE)
_LAVENDER = _hex_to_rgb(C_LAVENDER)
_SUBTEXT = _hex_to_rgb(C_SUBTEXT0)
_BORDER = _hex_to_rgb("#45475a")  # surface1


def _find_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        # Linux
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=0)
            except Exception:
                continue
    return ImageFont.load_default(size)


def _draw_rounded_rect(draw: ImageDraw.ImageDraw, xy, radius: int, fill, outline=None, width=1):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _parse_blocks(text: str) -> list[tuple[str, str]]:
    """Parse markdown text into typed blocks: (type, content).

    Types: heading, paragraph, list_item, blockquote, hr
    """
    blocks: list[tuple[str, str]] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("### "):
            blocks.append(("h3", stripped[4:]))
        elif stripped.startswith("## "):
            blocks.append(("h2", stripped[3:]))
        elif stripped.startswith("# "):
            blocks.append(("h1", stripped[2:]))
        elif stripped in ("---", "***", "___"):
            blocks.append(("hr", ""))
        elif stripped.startswith("> "):
            blocks.append(("blockquote", stripped[2:]))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            blocks.append(("list_item", stripped[2:]))
        elif len(stripped) > 2 and stripped[0].isdigit() and ". " in stripped[:5]:
            blocks.append(("list_item", stripped))
        else:
            blocks.append(("paragraph", stripped))
    return blocks


def _strip_md_inline(text: str) -> str:
    """Remove markdown inline formatting for plain text rendering."""
    import re
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text


def _col_width(wrap_w: int, body_size: int, indent: int = 0) -> int:
    """Shared column width calculation for both measurement and rendering."""
    char_w = max(1, int(body_size * 0.55))
    return max(10, (wrap_w - indent) // char_w)


def _measure_blocks(blocks, font_body, font_heading, font_small, max_w) -> int:
    """Calculate total image height needed for all blocks."""
    y = _PADDING + 40  # header space
    wrap_w = max(20, max_w - 2 * _PADDING)

    for btype, content in blocks:
        if btype == "hr":
            y += 12
            continue
        if btype in ("h1", "h2", "h3"):
            font = font_small if btype == "h3" else font_heading
            col_w = _col_width(wrap_w, font_body.size)
            lines = textwrap.wrap(_strip_md_inline(content), width=col_w)
            y += _HEADING_SPACING + len(lines) * (font.size + _LINE_SPACING)
        elif btype == "blockquote":
            col_w = _col_width(wrap_w, font_body.size, indent=20)
            lines = textwrap.wrap(_strip_md_inline(content), width=col_w)
            y += 8 + len(lines) * (font_body.size + _LINE_SPACING) + 8
        elif btype == "list_item":
            col_w = _col_width(wrap_w, font_body.size, indent=24)
            text = _strip_md_inline(content)
            lines = textwrap.wrap(text, width=col_w)
            y += len(lines) * (font_body.size + _LINE_SPACING) + 2
        else:
            col_w = _col_width(wrap_w, font_body.size)
            lines = textwrap.wrap(_strip_md_inline(content), width=col_w)
            y += len(lines) * (font_body.size + _LINE_SPACING) + 4

    y += _PADDING + 24  # footer
    return y


def render_interp_image(md_text: str) -> Image.Image:
    """Render markdown interpretation text to a Catppuccin-themed PNG image."""
    font_body = _find_font(16)
    font_heading = _find_font(22)
    font_small = _find_font(18)
    font_title = _find_font(28)
    font_footer = _find_font(12)

    blocks = _parse_blocks(md_text)
    max_w = _WIDTH
    total_h = _measure_blocks(blocks, font_body, font_heading, font_small, max_w)
    total_h = max(total_h, 200)

    img = Image.new("RGB", (max_w, total_h), _BG)
    draw = ImageDraw.Draw(img)

    # Header
    draw.text((_PADDING, _PADDING), "Nekomata", fill=_MAUVE, font=font_title)
    orn_y = _PADDING + 36
    draw.line([(_PADDING, orn_y), (max_w - _PADDING, orn_y)], fill=_BORDER, width=1)
    draw.text((max_w // 2 - 60, orn_y + 4), "─── ✦ ───", fill=_SUBTEXT, font=font_footer)

    y = orn_y + 24
    wrap_w = max(20, max_w - 2 * _PADDING)

    for btype, content in blocks:
        if btype == "hr":
            draw.line([(_PADDING, y + 4), (max_w - _PADDING, y + 4)], fill=_BORDER, width=1)
            y += 12
            continue

        if btype in ("h1", "h2", "h3"):
            font = font_small if btype == "h3" else font_heading
            color = _GOLD if btype in ("h1", "h2") else _MAUVE
            text = _strip_md_inline(content)
            col_w = _col_width(wrap_w, font_body.size)
            for line in textwrap.wrap(text, width=col_w):
                draw.text((_PADDING, y), line, fill=color, font=font)
                y += font.size + _LINE_SPACING
            y += _HEADING_SPACING - _LINE_SPACING
            continue

        if btype == "blockquote":
            text = _strip_md_inline(content)
            col_w = _col_width(wrap_w, font_body.size, indent=20)
            lines = textwrap.wrap(text, width=col_w)
            block_h = len(lines) * (font_body.size + _LINE_SPACING)
            draw.line(
                [(_PADDING + 4, y), (_PADDING + 4, y + block_h + 8)],
                fill=_MAUVE, width=2,
            )
            for line in lines:
                draw.text((_PADDING + 16, y + 4), line, fill=_SUBTEXT, font=font_body)
                y += font_body.size + _LINE_SPACING
            y += 8
            continue

        if btype == "list_item":
            text = _strip_md_inline(content)
            col_w = _col_width(wrap_w, font_body.size, indent=24)
            draw.text((_PADDING + 4, y), "•", fill=_LAVENDER, font=font_body)
            for line in textwrap.wrap(text, width=col_w):
                draw.text((_PADDING + 20, y), line, fill=_TEXT, font=font_body)
                y += font_body.size + _LINE_SPACING
            y += 2
            continue

        # paragraph
        text = _strip_md_inline(content)
        col_w = _col_width(wrap_w, font_body.size)
        for line in textwrap.wrap(text, width=col_w):
            draw.text((_PADDING, y), line, fill=_TEXT, font=font_body)
            y += font_body.size + _LINE_SPACING
        y += 4

    # Footer
    footer_text = "Generated by Nekomata ✦"
    draw.text((_PADDING, total_h - _PADDING - 14), footer_text, fill=_SUBTEXT, font=font_footer)

    return img


def save_image(img: Image.Image) -> str:
    """Save image to a temp file and return the path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp, "PNG")
    tmp.close()
    return tmp.name
