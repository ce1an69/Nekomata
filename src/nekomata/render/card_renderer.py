from __future__ import annotations

from pathlib import Path

from PIL import Image
from rich.panel import Panel
from rich.text import Text

from nekomata.card.types import Card, DrawnCard
from nekomata.render.themes import CardTheme, get_theme

# Card pixel sizes by layout mode
SIZES = {
    "full": (64, 96),
    "medium": (48, 72),
    "compact": (32, 48),
}


def get_preview_path(card: Card) -> Path | None:
    if card.image_path is None:
        return None
    return card.image_path.with_name(card.image_path.stem + "_detail.png")


def _load_card_image(card: Card, size: str = "compact", reversed: bool = False) -> Image.Image | None:
    """Load and resize a card PNG. Returns None if no image available."""
    if card.image_path is None or not card.image_path.exists():
        return None
    img = Image.open(card.image_path)
    if reversed:
        img = img.rotate(180)
    w, h = SIZES.get(size, SIZES["compact"])
    img = img.resize((w, h), Image.Resampling.NEAREST)
    return img


def _image_to_renderable(img: Image.Image):
    """Convert PIL Image to a Rich renderable via rich-pixels."""
    from rich_pixels import Pixels
    return Pixels.from_image(img)


def render_card_image(drawn: DrawnCard, size: str = "compact", theme: CardTheme | None = None) -> Panel | None:
    """Render a card as a pixel image panel. Returns None if no PNG available."""
    theme = theme or get_theme()
    img = _load_card_image(drawn.card, size, reversed=drawn.is_reversed)
    if img is None:
        return None
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border
    label = "逆位 ↕" if drawn.is_reversed else ""
    title = f"[{drawn.position.name_zh}] {drawn.card.name_zh} {label}"
    return Panel(
        _image_to_renderable(img),
        title=title,
        border_style=border_style,
        padding=(0, 1),
    )


def render_card_image_detail(drawn: DrawnCard, theme: CardTheme | None = None) -> Panel | None:
    """Render a card detail preview (128x192). Returns None if no PNG."""
    theme = theme or get_theme()
    preview_path = get_preview_path(drawn.card)
    if preview_path is None or not preview_path.exists():
        return None
    img = Image.open(preview_path)
    if drawn.is_reversed:
        img = img.rotate(180)
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border
    status = "逆位 ↕" if drawn.is_reversed else "正位"
    title = f"[{drawn.position.name_zh}] — {drawn.card.name_zh} ({status})"
    return Panel(
        _image_to_renderable(img),
        title=title,
        border_style=border_style,
        padding=(0, 1),
    )


def render_card_text(drawn: DrawnCard, width: int = 40, theme: CardTheme | None = None) -> Panel:
    theme = theme or get_theme()
    card = drawn.card
    reversal = " ↕ 逆位" if drawn.is_reversed else ""
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border

    content = Text()
    content.append(f"{card.name_zh} ({card.name}){reversal}\n\n")

    if drawn.is_reversed:
        content.append("逆位关键词：", style="bold")
        content.append(", ".join(card.keywords_reversed))
        content.append("\n\n")
        content.append(card.meaning_reversed)
    else:
        content.append("正位关键词：", style="bold")
        content.append(", ".join(card.keywords_upright))
        content.append("\n\n")
        content.append(card.meaning_upright)

    return Panel(
        content,
        title=f"[{drawn.position.name_zh}]",
        border_style=border_style,
        width=width,
        padding=(0, 1),
    )


def render_card_detail(drawn: DrawnCard, width: int = 60, theme: CardTheme | None = None) -> Panel:
    """Text-based detail view. PNG detail preview is in render_card_image_detail."""
    theme = theme or get_theme()
    card = drawn.card
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border
    status = "逆位 ↕" if drawn.is_reversed else "正位"

    content = Text()
    content.append(f"{card.name_zh} ({card.name})  [{status}]\n", style="bold")
    content.append(f"元素：{card.element}  ·  星座：{card.astrology}\n\n")

    content.append("正位关键词：", style="bold")
    content.append(", ".join(card.keywords_upright))
    content.append("\n")
    content.append(card.meaning_upright)
    content.append("\n\n")

    content.append("逆位关键词：", style="bold")
    content.append(", ".join(card.keywords_reversed))
    content.append("\n")
    content.append(card.meaning_reversed)

    return Panel(
        content,
        title=f"[{drawn.position.name_zh}] — {card.name_zh}",
        border_style=border_style,
        width=width,
        padding=(1, 2),
    )


def render_reading_summary(drawn_cards: list[DrawnCard], question: str, theme: CardTheme | None = None) -> Panel:
    theme = theme or get_theme()
    content = Text()
    content.append(f"🔮 {question}\n\n")
    for dc in drawn_cards:
        status = "逆位" if dc.is_reversed else "正位"
        content.append(f"【{dc.position.name_zh}】", style="bold")
        content.append(f" {dc.card.name_zh}（{status}）\n")
    return Panel(content, title="占卜结果", border_style=theme.summary_border)
