"""Draw screen widgets: DeckCard, SpreadSlot, ConfirmExitInterpretation."""

import asyncio

from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.css.scalar import ScalarOffset
from textual.geometry import Offset
from textual.message import Message
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Static

from nekomata.card.types import DrawnCard
from nekomata.render.animations import animate_entrance
from nekomata.render.card_renderer import create_card_face_widget
from nekomata.render.styles import (
    C_CRUST,
    C_LAVENDER,
    C_MANTLE,
    C_MAUVE,
    C_OVERLAY0,
    C_PINK,
    C_SUBTEXT0,
    C_SURFACE0,
    C_SURFACE1,
    C_SURFACE2,
    C_TEXT,
    EASE,
    EASE_SPRING,
    EASE_OUT,
)
from nekomata.render.themes import get_theme

# Deck layout constants
NUM_DECK_CARDS = 48
DECK_ROW_COUNT = 4
DECK_CARD_WIDTH = 9
DECK_CARD_HEIGHT = 7
SPREAD_SLOT_WIDTH = 16
SPREAD_SLOT_HEIGHT = 12

# Animation timing constants
DECK_HIDE_DELAY = 0.42
PICK_COMPLETE_DELAY = 0.35
SPREAD_RECENTER_OFFSET = 4
SPREAD_RECENTER_DURATION = 0.28
SLOT_PLACE_OFFSET = 2
SLOT_PLACE_DURATION = 0.22
SLOT_FLIP_FADE_OUT = 0.10
SLOT_FLIP_SWAP_PAUSE = 0.015
SLOT_FLIP_FADE_IN = 0.18
SLOT_FLIP_GLOW_HOLD = 0.08


class ConfirmExitInterpretation(ModalScreen[bool]):
    """Confirm leaving an active interpretation."""

    BINDINGS = [
        Binding("enter", "confirm", "确认退出"),
        Binding("escape", "cancel", "取消"),
        Binding("q", "cancel", "取消"),
    ]

    DEFAULT_CSS = f"""
    ConfirmExitInterpretation {{
        align: center middle;
        background: {C_CRUST};
    }}
    ConfirmExitInterpretation #confirm-card {{
        width: 54;
        height: auto;
        align: center middle;
        border: round {C_MAUVE};
        background: {C_MANTLE};
        padding: 1 2;
        transition: opacity 220ms {EASE}, offset 260ms {EASE};
    }}
    ConfirmExitInterpretation #confirm-content {{
        width: 1fr;
        height: auto;
        color: {C_TEXT};
        background: {C_MANTLE};
        text-align: center;
        content-align: center middle;
    }}
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-card"):
            content = Text(justify="center")
            content.append("退出解读？", style=f"bold {C_MAUVE}")
            content.append("\n\n")
            content.append("当前解读将停止，并直接返回首页。", style=C_TEXT)
            content.append("\n\n")
            content.append("Enter 确认退出 · Esc 取消", style=C_OVERLAY0)
            yield Static(content, id="confirm-content")

    def on_mount(self) -> None:
        animate_entrance(self.query_one("#confirm-card"), duration=0.24)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class DeckCard(Static):
    """A face-down card in the deck row — solid color back."""

    can_focus = True

    class Picked(Message):
        def __init__(self, card: "DeckCard") -> None:
            self.card = card
            super().__init__()

    DEFAULT_CSS = f"""
    DeckCard {{
        width: {DECK_CARD_WIDTH};
        height: {DECK_CARD_HEIGHT};
        min-width: {DECK_CARD_WIDTH};
        min-height: {DECK_CARD_HEIGHT};
        background: {C_SURFACE0};
        border: round {C_SURFACE0};
        content-align: center middle;
        padding: 0 0;
        margin: 0 1;
        transition: offset 300ms {EASE_OUT}, border 260ms {EASE_OUT}, background 260ms {EASE_OUT}, opacity 320ms {EASE_OUT};
    }}
    DeckCard:focus {{
        border: round {C_MAUVE};
        background: {C_SURFACE1};
        offset: 0 -1;
    }}
    DeckCard.picked {{
        border: round {C_PINK};
        background: {C_SURFACE1};
        opacity: 1;
        offset: 0 -1;
    }}
    DeckCard.exiting {{
        opacity: 0;
        offset: 0 -2;
    }}
    """

    def __init__(self, index: int) -> None:
        self.index = index
        super().__init__()

    def on_click(self) -> None:
        if self.has_class("picked"):
            return
        self.post_message(self.Picked(self))

    def key_enter(self) -> None:
        if self.has_class("picked"):
            return
        self.post_message(self.Picked(self))


class SpreadSlot(Widget):
    """A position slot in the spread: empty → face-down → revealed."""

    can_focus = True

    class Selected(Message):
        """Posted when a revealed slot is focused/clicked (for detail panel)."""

        def __init__(self, slot: "SpreadSlot") -> None:
            self.slot = slot
            super().__init__()

    class Flipped(Message):
        def __init__(self, slot: "SpreadSlot") -> None:
            self.slot = slot
            super().__init__()

    DEFAULT_CSS = f"""
    SpreadSlot {{
        width: {SPREAD_SLOT_WIDTH};
        height: {SPREAD_SLOT_HEIGHT};
        min-width: {SPREAD_SLOT_WIDTH};
        min-height: {SPREAD_SLOT_HEIGHT};
        background: {C_CRUST};
        border: round {C_SURFACE0};
        content-align: center middle;
        padding: 0 0;
        margin: 0 1;
        transition: opacity 280ms {EASE_OUT}, offset 220ms {EASE_SPRING}, border 260ms {EASE_OUT}, background 260ms {EASE_OUT};
    }}
    SpreadSlot:focus {{
        border: round {C_PINK};
        background: {C_SURFACE1};
    }}
    SpreadSlot.empty {{
        border: round {C_SURFACE1};
        background: {C_CRUST};
    }}
    SpreadSlot.waiting {{
        border: round {C_MAUVE};
    }}
    SpreadSlot.face-down {{
        background: {C_SURFACE0};
        border: round {C_SURFACE0};
    }}
    SpreadSlot.face-down:focus {{
        border: round {C_PINK};
        background: {C_SURFACE1};
    }}
    SpreadSlot.revealed {{
        background: {C_MANTLE};
        border: round {C_LAVENDER};
    }}
    SpreadSlot.reversed {{
        border: round {C_MAUVE};
    }}
    SpreadSlot.reversed:focus {{
        border: round {C_PINK};
    }}
    SpreadSlot.revealed:focus {{
        border: round {C_PINK};
        background: {C_SURFACE1};
    }}
    SpreadSlot.selected {{
        border: round {C_LAVENDER};
    }}
    SpreadSlot.selected:focus {{
        border: round {C_PINK};
        background: {C_SURFACE1};
    }}
    SpreadSlot.glow {{
        border: round {C_PINK};
        background: {C_SURFACE0};
    }}
    SpreadSlot .card-face {{
        width: 100%;
        height: 100%;
    }}
    SpreadSlot .slot-content {{
        width: auto;
        height: auto;
        background: transparent;
    }}
    """

    def __init__(self, position_index: int, position_name_zh: str) -> None:
        self.position_index = position_index
        self.position_name_zh = position_name_zh
        self.drawn_card: DrawnCard | None = None
        self.is_revealed = False
        super().__init__()

    def compose(self) -> ComposeResult:
        content = Group(
            Text("?", style=f"bold {C_SURFACE1}", justify="center"),
            Text(self.position_name_zh, style=C_SURFACE2, justify="center"),
        )
        yield Static(content, classes="slot-content")

    def _build_reveal_content(self):
        """Build the Rich renderable for the revealed state."""
        if not self.drawn_card:
            return None
        dc = self.drawn_card

        if self.app.render_mode != "text":
            img_widget = create_card_face_widget(dc)
            if img_widget is not None:
                return img_widget

        border_style = C_LAVENDER if dc.is_reversed else C_MAUVE
        status_style = C_PINK if dc.is_reversed else C_MAUVE
        return Panel(
            Group(
                Text(dc.card.name_zh, style=f"bold {C_TEXT}", justify="center"),
                Text(dc.status_label, style=status_style, justify="center"),
            ),
            border_style=border_style,
            padding=(0, 0),
            width=8,
            height=5,
        )

    def place_card(self, drawn_card: DrawnCard) -> None:
        self.drawn_card = drawn_card
        self.remove_class("empty")
        self.add_class("face-down")
        # Pre-build and pre-mount the reveal widget (hidden) for zero-latency flip
        reveal = self._build_reveal_content()
        if reveal is not None:
            if isinstance(reveal, Widget):
                reveal.display = False
                self._mount_reveal(reveal)
            else:
                self._mount_reveal(Static(reveal, classes="slot-reveal", display=False))
        # Show face-down label
        label = self.query_one(".slot-content", Static)
        label.display = True
        label.update(Text(self.position_name_zh, style=C_SUBTEXT0, justify="center"))

    def _mount_reveal(self, widget: Widget) -> None:
        """Mount the pre-built reveal widget (called from place_card)."""
        self.mount(widget)

    def _render_revealed(self) -> None:
        """Swap to revealed content: hide face-down, show pre-mounted reveal."""
        if not self.drawn_card:
            return
        dc = self.drawn_card
        if dc.is_reversed:
            self.add_class("reversed")
        else:
            self.remove_class("reversed")
        # Hide face-down content
        try:
            self.query_one(".slot-content").display = False
        except Exception:
            pass
        # Show pre-mounted reveal widget
        for child in self.children:
            if not child.has_class("slot-content"):
                child.display = True
                return

    async def flip(self) -> None:
        """Animate a card flip: fade-out → swap content → spring fade-in with glow."""
        self.styles.animate("opacity", 0.0, duration=SLOT_FLIP_FADE_OUT, easing=EASE)
        self.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, -1)),
            duration=SLOT_FLIP_FADE_OUT,
            easing=EASE,
        )
        await asyncio.sleep(SLOT_FLIP_FADE_OUT)

        self.is_revealed = True
        self.remove_class("face-down")
        self.add_class("revealed")
        self._render_revealed()
        self.styles.opacity = 0
        self.styles.offset = (0, 1)

        await asyncio.sleep(SLOT_FLIP_SWAP_PAUSE)
        self.styles.animate("opacity", 1.0, duration=SLOT_FLIP_FADE_IN, easing=EASE)
        self.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, 0)),
            duration=SLOT_FLIP_FADE_IN,
            easing=EASE_SPRING,
        )
        self.add_class("glow")

        await asyncio.sleep(SLOT_FLIP_FADE_IN + SLOT_FLIP_GLOW_HOLD)
        self.remove_class("glow")

    def on_click(self) -> None:
        if self.drawn_card and not self.is_revealed:
            self.post_message(self.Flipped(self))
        elif self.is_revealed:
            self.post_message(self.Selected(self))

    def key_enter(self) -> None:
        if self.drawn_card and not self.is_revealed:
            self.post_message(self.Flipped(self))
        elif self.is_revealed:
            self.post_message(self.Selected(self))

    def on_focus(self) -> None:
        if self.is_revealed:
            self.post_message(self.Selected(self))
