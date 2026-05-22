"""Card rendering pipeline: PNG images via rich-pixels with text fallback."""


from pathlib import Path

from PIL import Image
from rich.console import Group
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
    "preview": (56, 84),
    "slot": (16, 24),
    "detail_panel": (40, 60),
    "origin_panel": (128, 192),
}


def get_preview_path(card: Card) -> Path | None:
    """Return the path to the detail preview PNG for a card, or None."""
    if card.image_path is None:
        return None
    return card.image_path.with_name(card.image_path.stem + "_detail.png")


def get_origin_path(card: Card) -> Path | None:
    """Return the path to the high-resolution origin PNG for a card, or None."""
    if card.image_path is None:
        return None
    return card.image_path.with_name(card.image_path.stem + "_origin.png")


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


def _load_card_detail_image(
    card: Card,
    upside_down: bool = False,
    size: str = "preview",
) -> Image.Image | None:
    """Load and resize the detail preview PNG. Returns None if no preview exists."""
    preview_path = get_preview_path(card)
    if preview_path is None or not preview_path.exists():
        return None
    img = Image.open(preview_path)
    if upside_down:
        img = img.rotate(180)
    w, h = SIZES.get(size, SIZES["preview"])
    return img.resize((w, h), Image.Resampling.NEAREST)


def _load_card_face_image(card: Card, size: str = "compact", upside_down: bool = False) -> Image.Image | None:
    """Load detail variant for spread face. Falls back to base image."""
    detail_path = get_preview_path(card)
    if detail_path is not None and detail_path.exists():
        img = Image.open(detail_path)
        if upside_down:
            img = img.rotate(180)
        w, h = SIZES.get(size, SIZES["compact"])
        return img.resize((w, h), Image.Resampling.NEAREST)
    return _load_card_image(card, size, upside_down)


def _load_card_origin_image(
    card: Card,
    upside_down: bool = False,
    size: str = "origin_panel",
) -> Image.Image | None:
    """Load and resize the high-resolution origin PNG. Returns None if no origin exists."""
    origin_path = get_origin_path(card)
    if origin_path is None or not origin_path.exists():
        return None
    img = Image.open(origin_path)
    if upside_down:
        img = img.rotate(180)
    w, h = SIZES.get(size, SIZES["origin_panel"])
    return img.resize((w, h), Image.Resampling.LANCZOS)


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


def render_card_face(drawn: DrawnCard, size: str = "compact", theme: CardTheme | None = None) -> Panel | None:
    """Render only the card face for spread layouts (detail variant). Returns None if no PNG exists."""
    theme = theme or get_theme()
    img = _load_card_face_image(drawn.card, size, upside_down=drawn.is_reversed)
    if img is None:
        return None
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border
    return Panel(
        _image_to_renderable(img),
        border_style=border_style,
        padding=(0, 0),
    )


def render_card_image_detail(
    drawn: DrawnCard,
    theme: CardTheme | None = None,
    size: str = "detail_panel",
) -> Panel | None:
    """Render a card detail preview from _detail.png variant. Returns None if no PNG."""
    theme = theme or get_theme()
    img = _load_card_detail_image(drawn.card, upside_down=drawn.is_reversed, size=size)
    if img is None:
        return None
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border
    title = f"[{drawn.position.name}] — {drawn.card.name_zh} ({drawn.status_label})"
    return Panel(
        _image_to_renderable(img),
        title=title,
        border_style=border_style,
        padding=(0, 0),
    )


def render_card_image_origin(
    drawn: DrawnCard,
    theme: CardTheme | None = None,
    size: str = "origin_panel",
) -> Panel | None:
    """Render a card detail preview from _origin.png variant. Returns None if no PNG."""
    theme = theme or get_theme()
    img = _load_card_origin_image(drawn.card, upside_down=drawn.is_reversed, size=size)
    if img is None:
        return None
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border
    title = f"[{drawn.position.name}] — {drawn.card.name_zh} ({drawn.status_label})"
    return Panel(
        _image_to_renderable(img),
        title=title,
        border_style=border_style,
        padding=(0, 1),
    )


def render_card_full_detail(drawn: DrawnCard, theme: CardTheme | None = None) -> Group | None:
    """Render origin image + text description for the detail panel."""
    theme = theme or get_theme()
    card = drawn.card

    img_panel = render_card_image_origin(drawn, theme)
    if img_panel is None:
        return None

    text = Text()
    text.append(f"{card.name_zh} ({card.name})  [{drawn.status_label}]\n", style="bold")
    text.append(f"Element: {card.element}  ·  Astrology: {card.astrology}\n\n")

    text.append("Upright: ", style="bold")
    text.append(", ".join(card.keywords_upright))
    text.append("\n")
    text.append(card.meaning_upright)
    text.append("\n\n")

    text.append("Reversed: ", style="bold")
    text.append(", ".join(card.keywords_reversed))
    text.append("\n")
    text.append(card.meaning_reversed)

    text_panel = Panel(
        text,
        border_style="none",
        padding=(0, 0),
    )
    return Group(img_panel, text_panel)


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
