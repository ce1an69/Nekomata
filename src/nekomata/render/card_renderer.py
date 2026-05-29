"""Card rendering pipeline: PNG images via textual-image with async preloading."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from PIL import Image as PILImage
from PIL import ImageChops
from PIL import ImageDraw
from rich.panel import Panel
from rich.text import Text

from nekomata.card.display import card_keywords, card_meaning, card_name, status_label
from nekomata.card.types import Card, DrawnCard
from nekomata.render.themes import get_theme
from nekomata.i18n import ui_section as section

_ORIGIN_MAX_SIZE = (1024, 1536)
_DETAIL_MAX_SIZE = (256, 384)

# Intentional module-level mutable state: image caches are managed by clear_cache()
# and keyed by card ID + reversal state. Safe for single-threaded TUI / CLI.
_image_cache: dict[str, PILImage.Image] = {}
_origin_cache: dict[str, PILImage.Image] = {}

# Intentional module-level mutable state: written once on first call.
_CACHED_TUI_CLASS = None

# Terminals with working TGP (Kitty Graphics Protocol) diacritic support.
_TGP_TERMINALS = {"kitty", "ghostty", "contour"}


def _get_tui_image_class():
    """Select the best image widget for the current terminal (cached)."""
    global _CACHED_TUI_CLASS
    if _CACHED_TUI_CLASS is not None:
        return _CACHED_TUI_CLASS
    from textual_image.widget import Image as AutoImage, TGPImage

    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    if term_program in _TGP_TERMINALS or os.environ.get("KITTY_WINDOW_ID"):
        _CACHED_TUI_CLASS = TGPImage
    else:
        _CACHED_TUI_CLASS = AutoImage
    return _CACHED_TUI_CLASS


def get_preview_path(card: Card) -> Path | None:
    """Return the path to the detail preview PNG for a card, or None."""
    if card.image_path is None:
        return None
    return card.image_path.with_name(card.image_path.stem + "_detail.png")


def get_origin_path(card: Card) -> Path | None:
    """Return the path to the origin PNG for a card, or None."""
    if card.image_path is None:
        return None
    return card.image_path.with_name(card.image_path.stem + "_origin.png")


def _load_image(
    path: Path | None,
    upside_down: bool = False,
    max_size: tuple[int, int] = _ORIGIN_MAX_SIZE,
) -> PILImage.Image | None:
    """Load a PNG, optionally rotate for reversal, and thumbnail to max_size."""
    if path is None or not path.exists():
        return None
    with PILImage.open(path) as source:
        img = source.copy()
    if upside_down:
        img = img.rotate(180)
    img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
    return img


def _load_runtime_image(card: Card, upside_down: bool = False, *, rounded: bool = True) -> PILImage.Image | None:
    """Load the smaller runtime image, falling back to capped origin if needed."""
    img = _load_image(get_preview_path(card), upside_down, _DETAIL_MAX_SIZE)
    if img is not None:
        return _with_rounded_corners(img) if rounded else img
    img = _load_image(get_origin_path(card), upside_down, _DETAIL_MAX_SIZE)
    if img is None:
        return None
    return _with_rounded_corners(img) if rounded else img


def _with_rounded_corners(img: PILImage.Image) -> PILImage.Image:
    """Clip spread cards to rounded corners so the image matches the slot shape."""
    rounded = img.convert("RGBA")
    radius = max(2, min(rounded.size) // 14)
    mask = PILImage.new("L", rounded.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, rounded.width, rounded.height), radius=radius, fill=255)
    rounded.putalpha(ImageChops.multiply(rounded.getchannel("A"), mask))
    return rounded


def _cache_key(card: Card, is_reversed: bool) -> str:
    """Return a cache key for a card + reversal state."""
    suffix = ":rev" if is_reversed else ""
    return f"{card.id}{suffix}"


# ── Preload API ──────────────────────────────────────────────────────


def preload_card_image(card: Card, is_reversed: bool = False) -> None:
    """Load and cache the runtime image for a card. Call from a worker thread."""
    key = _cache_key(card, is_reversed)
    if key in _image_cache:
        return
    img = _load_runtime_image(card, upside_down=is_reversed)
    if img is not None:
        _image_cache[key] = img


async def preload_card_image_async(card: Card, is_reversed: bool = False) -> None:
    """Async wrapper for preload_card_image. Runs in a thread pool."""
    await asyncio.to_thread(preload_card_image, card, is_reversed)


async def preload_all_async(cards: list[tuple[Card, bool]]) -> None:
    """Preload multiple images in parallel. Returns when all are cached."""
    await asyncio.gather(*(preload_card_image_async(c, rev) for c, rev in cards))


def get_cached_image(card: Card, is_reversed: bool = False) -> PILImage.Image | None:
    """Return a cached PIL image, or None if not yet loaded."""
    return _image_cache.get(_cache_key(card, is_reversed))


def clear_cache() -> None:
    """Clear all image caches (e.g., on screen unmount)."""
    _image_cache.clear()
    _origin_cache.clear()


# ── Widget-based API (textual-image) ─────────────────────────────────


def create_card_face_widget(drawn: DrawnCard):
    """Return an Image widget for the spread slot face, or None if no image.

    Uses preloaded cache; falls back to synchronous load if cache miss.
    """
    img = get_cached_image(drawn.card, drawn.is_reversed)
    if img is None:
        img = _load_runtime_image(drawn.card, upside_down=drawn.is_reversed)
    if img is None:
        return None
    TUIImage = _get_tui_image_class()
    return TUIImage(img, classes="card-face")


def create_card_origin_widget(drawn: DrawnCard):
    """Return an Image widget for the origin detail image, or None if no PNG.

    Always shows the upright (non-reversed) orientation regardless of
    the drawn card's reversed state.
    """
    key = _cache_key(drawn.card, is_reversed=False)
    img = _origin_cache.get(key)
    if img is None:
        img = _load_runtime_image(drawn.card, upside_down=False, rounded=False)
        if img is not None:
            _origin_cache[key] = img
    if img is None:
        return None
    TUIImage = _get_tui_image_class()
    return TUIImage(img, classes="card-origin")


def _build_detail_text(drawn: DrawnCard, lang: str = "en") -> Text:
    """Build the rich Text content for a card's full detail view."""
    labels = section("card_detail", lang)
    card = drawn.card
    text = Text()
    text.append(f"{card_name(card, lang)}  [{status_label(drawn.is_reversed, lang)}]\n", style="bold")
    text.append(f"{labels['element']}: {card.element}  ·  {labels['astrology']}: {card.astrology}\n\n")

    text.append(f"{labels['upright']}: ", style="bold")
    text.append(", ".join(card_keywords(card, False, lang)))
    text.append("\n")
    text.append(card_meaning(card, False, lang))
    text.append("\n\n")

    text.append(f"{labels['reversed']}: ", style="bold")
    text.append(", ".join(card_keywords(card, True, lang)))
    text.append("\n")
    text.append(card_meaning(card, True, lang))
    return text


def render_card_full_detail_widgets(drawn: DrawnCard, lang: str = "en") -> tuple[object, Panel] | None:
    """Return (image_widget, text_panel) for the detail view, or None if no image."""
    img_widget = create_card_origin_widget(drawn)
    if img_widget is None:
        return None

    text_panel = Panel(
        _build_detail_text(drawn, lang),
        border_style="none",
        padding=(0, 0),
    )
    return (img_widget, text_panel)


# ── Text fallback ────────────────────────────────────────────────────


def render_card_text(drawn: DrawnCard, width: int = 40, lang: str = "en") -> Panel:
    """Render a card as a text panel (fallback when no PNG is available)."""
    theme = get_theme()
    card = drawn.card
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border

    content = Text()
    reversal = " ↕" if drawn.is_reversed else ""
    content.append(f"{card.name_zh} ({card.name}){reversal}\n\n")
    content.append(f"{status_label(drawn.is_reversed, lang)}: ", style="bold")
    content.append(", ".join(card_keywords(card, drawn.is_reversed, lang)))
    content.append("\n\n")
    content.append(card_meaning(card, drawn.is_reversed, lang))

    return Panel(
        content,
        title=f"[{drawn.position.name}]",
        border_style=border_style,
        width=width,
        padding=(0, 1),
    )


def render_card_detail(drawn: DrawnCard, width: int = 60, lang: str = "en") -> Panel:
    """Text-based detail view showing both upright and reversed meanings."""
    theme = get_theme()
    border_style = theme.reversed_border if drawn.is_reversed else theme.upright_border

    return Panel(
        _build_detail_text(drawn, lang),
        title=card_name(drawn.card, lang),
        border_style=border_style,
        width=width,
        padding=(1, 2),
    )
