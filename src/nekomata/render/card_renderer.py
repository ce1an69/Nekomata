"""Card rendering pipeline: PNG images via rich-pixels with text fallback."""


from pathlib import Path

from PIL import Image
from rich.panel import Panel
from rich.text import Text
from rich_pixels import Pixels

from nekomata.card.types import Card, DrawnCard
from nekomata.render.themes import CardTheme, get_theme

# Card pixel sizes by layout mode
SIZES = {
    "full": (64, 96),
    "medium": (48, 72),
    "compact": (32, 48),
}


def get_preview_path(card: Card) -> Path | None:
    """Return the path to the detail preview PNG for a card, or None."""
    if card.image_path is None:
        return None
    return card.image_path.with_name(card.image_path.stem + "_detail.png")


def _load_card_image(card: Card, size: str = "compact", upside_down: bool = False) -> Image.Image | None:
    """Load and resize a card PNG. Returns None if no image available."""
    if card.image_path is None or not card.image_path.exists():
        return None
    img = Image.open(card.image_path)
    if upside_down:
        img = img.rotate(180)
    w, h = SIZES.get(size, SIZES["compact"])
    img = img.resize((w, h), Image.Resampling.NEAREST)
    return img


def _image_to_renderable(img: Image.Image) -> Pixels:
    """Convert PIL Image to a Rich renderable via rich-pixels."""
    return Pixels.from_image(img)


def render_card_image(drawn: DrawnCard, size: str = "compact", theme: CardTheme | None = None) -> Panel | None:
    """Render a card as a pixel image panel. Returns None if no PNG available."""
    theme = theme or get_theme()
    img = _load_card_image(drawn.card, size, upside_down=drawn.is_reversed)
    if img is None:
        return None
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border
    label = " ↕" if drawn.is_reversed else ""
    title = f"[{drawn.position.name}] {drawn.card.name}{label}"
    return Panel(
        _image_to_renderable(img),
        title=title,
        border_style=border_style,
        padding=(0, 1),
    )


def render_card_image_detail(drawn: DrawnCard, theme: CardTheme | None = None) -> Panel | None:
    """Render a card detail preview from _detail.png variant. Returns None if no PNG."""
    theme = theme or get_theme()
    preview_path = get_preview_path(drawn.card)
    if preview_path is None or not preview_path.exists():
        return None
    img = Image.open(preview_path)
    if drawn.is_reversed:
        img = img.rotate(180)
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border
    title = f"[{drawn.position.name}] — {drawn.card.name_zh} ({drawn.status_label})"
    return Panel(
        _image_to_renderable(img),
        title=title,
        border_style=border_style,
        padding=(0, 1),
    )


def render_card_text(drawn: DrawnCard, width: int = 40, theme: CardTheme | None = None) -> Panel:
    """Render a card as a text panel (fallback when no PNG is available)."""
    theme = theme or get_theme()
    card = drawn.card
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border

    content = Text()
    reversal = " ↕" if drawn.is_reversed else ""
    content.append(f"{card.name_zh} ({card.name}){reversal}\n\n")
    content.append(f"{drawn.status_label}: ", style="bold")
    content.append(", ".join(drawn.keywords))
    content.append("\n\n")
    content.append(drawn.meaning)

    return Panel(
        content,
        title=f"[{drawn.position.name}]",
        border_style=border_style,
        width=width,
        padding=(0, 1),
    )


def render_card_detail(drawn: DrawnCard, width: int = 60, theme: CardTheme | None = None) -> Panel:
    """Text-based detail view showing both upright and reversed meanings."""
    theme = theme or get_theme()
    card = drawn.card
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border

    content = Text()
    content.append(f"{card.name_zh} ({card.name})  [{drawn.status_label}]\n", style="bold")
    content.append(f"Element: {card.element}  ·  Astrology: {card.astrology}\n\n")

    content.append("Upright: ", style="bold")
    content.append(", ".join(card.keywords_upright))
    content.append("\n")
    content.append(card.meaning_upright)
    content.append("\n\n")

    content.append("Reversed: ", style="bold")
    content.append(", ".join(card.keywords_reversed))
    content.append("\n")
    content.append(card.meaning_reversed)

    return Panel(
        content,
        title=f"[{drawn.position.name}] — {card.name_zh}",
        border_style=border_style,
        width=width,
        padding=(1, 2),
    )
