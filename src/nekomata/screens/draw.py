"""Draw screen — pick cards from a face-down deck, then flip to reveal."""

import asyncio
from collections import deque
from enum import Enum, auto

from rich.align import Align
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.css.scalar import ScalarOffset
from textual.css.query import NoMatches
from textual.events import Key
from textual.geometry import Offset
from textual.message import Message
from textual.screen import ModalScreen
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, Static

from nekomata.ai.interpreter import InterpretationError, StreamChunk, get_interpreter
from nekomata.card.deck import Deck
from nekomata.card.types import DrawnCard
from nekomata.render.card_renderer import (
    render_card_detail,
    render_card_face,
    render_card_image_detail,
)
from nekomata.render.themes import get_theme
from nekomata.screens.widgets import go_home
from nekomata.spread import get_spread

# Catppuccin Mocha palette
C_CRUST = "#11111b"
C_BASE = "#11111b"
C_MANTLE = "#181825"
C_SURFACE0 = "#313244"
C_SURFACE1 = "#45475a"
C_SURFACE2 = "#585b70"
C_OVERLAY0 = "#6c7086"
C_SUBTEXT0 = "#a6adc8"
C_TEXT = "#cdd6f4"
C_MAUVE = "#cba6f7"
C_LAVENDER = "#b4befe"
C_PINK = "#f5c2e7"
C_RED = "#f38ba8"

NUM_DECK_CARDS = 24
DECK_ROW_COUNT = 3

# Easing for smooth animations
_EASE = "out_cubic"
DECK_CARD_WIDTH = 10
DECK_CARD_HEIGHT = 8
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
STREAM_TYPE_INTERVAL = 0.025
STREAM_CHARS_PER_TICK = 3
DETAIL_PANEL_WIDTH = 66
INTERP_PANEL_HEIGHT = "46%"
INTERP_MIN_HEIGHT = 14
INTERP_MAX_HEIGHT = 30
INTERP_SIDE_MARGIN = 1
INTERP_DETAIL_GAP = 0
INTERP_FULL_SIDE_MARGIN = 5
INTERP_FULL_WIDTH_CORRECTION = 4


class Phase(Enum):
    PICK = auto()
    FLIP = auto()
    DONE = auto()


class ConfirmExitInterpretation(ModalScreen[bool]):
    """Confirm leaving an active interpretation."""

    BINDINGS = [
        Binding("escape", "cancel", "取消"),
        Binding("q", "cancel", "取消"),
    ]

    DEFAULT_CSS = f"""
    ConfirmExitInterpretation {{
        align: center middle;
        background: {C_CRUST} 70%;
    }}
    ConfirmExitInterpretation #confirm-card {{
        width: 54;
        height: auto;
        border: round {C_MAUVE};
        background: {C_MANTLE};
        padding: 1 2;
        transition: opacity 220ms {_EASE}, offset 260ms {_EASE};
    }}
    ConfirmExitInterpretation #confirm-title {{
        color: {C_MAUVE};
        text-style: bold;
        text-align: center;
        margin: 0 0 1 0;
    }}
    ConfirmExitInterpretation #confirm-message {{
        color: {C_TEXT};
        text-align: center;
        margin: 0 0 1 0;
    }}
    ConfirmExitInterpretation #confirm-hint {{
        color: {C_OVERLAY0};
        text-align: center;
        margin: 0 0 1 0;
    }}
    ConfirmExitInterpretation #confirm-actions {{
        height: auto;
        align: center middle;
    }}
    ConfirmExitInterpretation Button {{
        background: {C_BASE};
        color: {C_MAUVE};
        border: round {C_MAUVE};
        transition: background 160ms {_EASE}, border 160ms {_EASE}, color 160ms {_EASE}, offset 160ms {_EASE};
    }}
    ConfirmExitInterpretation Button:hover {{
        background: {C_SURFACE0};
        color: {C_TEXT};
        border: round {C_MAUVE};
    }}
    ConfirmExitInterpretation Button:focus {{
        background: {C_SURFACE0};
        color: {C_MAUVE};
        border: round {C_PINK};
        text-style: bold;
        offset: 0 -1;
    }}
    ConfirmExitInterpretation Button.-primary {{
        background: {C_BASE};
        color: {C_PINK};
        border: round {C_PINK};
    }}
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-card"):
            yield Static("退出解读？", id="confirm-title")
            yield Static("当前解读将停止，并直接返回首页。", id="confirm-message")
            yield Static("Esc / Q 取消", id="confirm-hint")
            with Center(id="confirm-actions"):
                yield Button("取消", id="cancel-exit")
                yield Button("确认退出", id="confirm-exit", classes="-primary")

    def on_mount(self) -> None:
        card = self.query_one("#confirm-card")
        if self.app.animation_enabled:
            card.styles.opacity = 0
            card.styles.offset = (0, 1)
            card.styles.animate("opacity", 1.0, duration=0.22, easing=_EASE)
            card.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 0)),
                duration=0.26,
                easing=_EASE,
            )
        self.query_one("#confirm-exit", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-exit")

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
        transition: offset 300ms {_EASE}, border 260ms {_EASE}, background 260ms {_EASE}, opacity 320ms {_EASE};
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


class SpreadSlot(Static):
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
        width: {DECK_CARD_WIDTH};
        height: {DECK_CARD_HEIGHT};
        min-width: {DECK_CARD_WIDTH};
        min-height: {DECK_CARD_HEIGHT};
        background: {C_CRUST};
        border: round {C_SURFACE0};
        content-align: center middle;
        padding: 0 0;
        margin: 0 1;
        transition: opacity 280ms {_EASE}, offset 220ms {_EASE}, border 260ms {_EASE}, background 260ms {_EASE};
    }}
    SpreadSlot:focus {{
        border: round {C_MAUVE};
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
    }}
    SpreadSlot.revealed {{
        background: {C_MANTLE};
        border: round {C_LAVENDER};
    }}
    SpreadSlot.revealed:focus {{
        border: round {C_MAUVE};
    }}
    SpreadSlot.glow {{
        border: round {C_PINK};
        background: {C_SURFACE0};
    }}
    """

    def __init__(self, position_index: int, position_name_zh: str) -> None:
        self.position_index = position_index
        self.position_name_zh = position_name_zh
        self.drawn_card: DrawnCard | None = None
        self.is_revealed = False
        super().__init__()
        self._render_empty()

    def _render_empty(self) -> None:
        self.update(
            Align.center(
                Group(
                    Text("?", style=f"bold {C_SURFACE1}", justify="center"),
                    Text(self.position_name_zh, style=C_SURFACE2, justify="center"),
                )
            )
        )

    def _render_face_down(self) -> None:
        label = Text(self.position_name_zh, style=C_SUBTEXT0, justify="center")
        self.update(Align.center(label))

    def _render_revealed(self) -> None:
        if not self.drawn_card:
            return
        dc = self.drawn_card
        theme = get_theme()
        render_mode = self.app.render_mode

        face = render_card_face(dc, size=render_mode, theme=theme)
        if face is None:
            border_style = C_LAVENDER if dc.is_reversed else C_MAUVE
            status_style = C_PINK if dc.is_reversed else C_MAUVE
            face = Panel(
                Group(
                    Text(dc.card.name_zh, style=f"bold {C_TEXT}", justify="center"),
                    Text(dc.status_label, style=status_style, justify="center"),
                ),
                border_style=border_style,
                padding=(0, 0),
                width=8,
                height=5,
            )
        self.update(Align.center(face))

    def place_card(self, drawn_card: DrawnCard) -> None:
        self.drawn_card = drawn_card
        self.remove_class("empty")
        self.add_class("face-down")
        self._render_face_down()

    async def flip(self) -> None:
        """Animate a card flip: soften → swap → settle with glow."""
        self.styles.offset = (0, -1)
        self.styles.animate("opacity", 0.12, duration=SLOT_FLIP_FADE_OUT, easing=_EASE)
        self.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, -1)),
            duration=SLOT_FLIP_FADE_OUT,
            easing=_EASE,
        )
        await asyncio.sleep(SLOT_FLIP_FADE_OUT)

        self.is_revealed = True
        self.remove_class("face-down")
        self.add_class("revealed")
        self._render_revealed()
        self.styles.opacity = 0.12
        self.styles.offset = (0, 1)

        await asyncio.sleep(SLOT_FLIP_SWAP_PAUSE)
        self.styles.animate("opacity", 1.0, duration=SLOT_FLIP_FADE_IN, easing=_EASE)
        self.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, 0)),
            duration=SLOT_FLIP_FADE_IN,
            easing=_EASE,
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


class DrawScreen(Screen):
    """Card drawing screen: pick from deck → flip to reveal → detail + interpret."""

    BINDINGS = [
        Binding("q", "handle_back", "返回"),
        Binding("escape", "handle_back", "返回"),
        Binding("i", "interpret", "解读", show=False),
        Binding("d", "toggle_detail", "详情", show=False),
    ]

    DEFAULT_CSS = f"""
    DrawScreen {{
        align: center top;
    }}
    #draw-header {{
        text-align: center;
        height: auto;
        margin-bottom: 0;
    }}
    #draw-divider {{
        color: {C_SURFACE2};
        text-align: center;
        height: 1;
    }}
    #draw-title {{
        color: {C_MAUVE};
        text-style: bold;
        text-align: center;
    }}
    #draw-question {{
        color: {C_SUBTEXT0};
        text-align: center;
    }}
    #deck-section {{
        height: auto;
        min-height: 32;
        padding: 0 1;
        margin: 0 0;
        border-bottom: solid {C_SURFACE0};
        background: {C_CRUST};
        transition: opacity 420ms {_EASE}, offset 420ms {_EASE};
    }}
    #deck-label {{
        background: {C_CRUST};
        color: {C_LAVENDER};
        text-style: bold;
        text-align: center;
        margin: 0 0 1 0;
    }}
    #deck-row {{
        height: auto;
        padding: 0 1;
        align: center middle;
    }}
    .deck-row-line {{
        height: auto;
        margin: 0 0 1 0;
        align: center middle;
    }}
    #main-area {{
        height: 1fr;
        margin-top: 0;
        transition: offset 280ms {_EASE};
    }}
    #spread-area {{
        width: 1fr;
        height: 1fr;
        padding: 1 0;
        align: center middle;
    }}
    #spread-label {{
        color: {C_LAVENDER};
        text-style: bold;
        text-align: center;
        margin: 0 0 1 0;
    }}
    #spread-grid {{
        height: auto;
        align: center middle;
    }}
    #spread-grid.layout-1 {{
        layout: grid;
        grid-size: 1;
        grid-columns: 12;
    }}
    #spread-grid.layout-3 {{
        layout: grid;
        grid-size: 3 1;
        grid-columns: 12 12 12;
    }}
    #spread-grid.layout-5 {{
        layout: grid;
        grid-size: 3 2;
        grid-columns: 12 12 12;
        grid-rows: 1fr 1fr;
    }}
    #spread-grid.layout-10 {{
        layout: grid;
        grid-size: 5 2;
        grid-columns: 12 12 12 12 12;
        grid-rows: 1fr 1fr;
    }}
    #card-preview {{
        dock: right;
        width: {DETAIL_PANEL_WIDTH};
        min-width: {DETAIL_PANEL_WIDTH};
        height: 100%;
        border: round {C_SURFACE0};
        background: {C_MANTLE};
        padding: 1 1;
        overflow: hidden;
        opacity: 0;
        display: none;
        offset: 4 0;
        transition: opacity 240ms {_EASE}, offset 320ms {_EASE};
    }}
    #preview-content {{
        background: {C_MANTLE};
    }}
    #card-preview.visible {{
        display: block;
        opacity: 1;
        offset: 0 0;
    }}
    #draw-footer {{
        dock: bottom;
        height: 1;
        color: {C_OVERLAY0};
        text-align: center;
        padding: 0 2;
    }}
    #interp-dialog {{
        dock: bottom;
        width: 1fr;
        height: {INTERP_PANEL_HEIGHT};
        min-height: {INTERP_MIN_HEIGHT};
        max-height: {INTERP_MAX_HEIGHT};
        display: none;
        border: round {C_MAUVE};
        background: {C_MANTLE};
        padding: 0 1;
        margin: 0 1 1 1;
        opacity: 0;
        offset: 0 2;
        transition: opacity 240ms {_EASE}, offset 320ms {_EASE}, width 220ms {_EASE};
    }}
    #interp-dialog.visible {{
        display: block;
        opacity: 1;
        offset: 0 0;
    }}
    #interp-dialog-title {{
        color: {C_MAUVE};
        text-style: bold;
        height: 1;
        margin: 0;
    }}
    #interp-dialog-content {{
        color: {C_TEXT};
        margin: 0;
    }}
    #interp-dialog-hints {{
        color: {C_OVERLAY0};
        height: 1;
        margin: 0;
    }}
    #status {{
        text-align: center;
        color: {C_MAUVE};
        height: auto;
    }}
    """

    def __init__(self, spread_key: str, question: str) -> None:
        super().__init__()
        self._spread_key = spread_key
        self._question = question
        self._spread = get_spread(spread_key)
        self._deck = Deck()
        self._deck.shuffle()
        self._planned_cards: list[DrawnCard] = []
        self._drawn_cards: list[DrawnCard] = []
        self._pick_index = 0
        self._phase = Phase.PICK
        self._cancelled = False
        self._interp_streaming = False
        self._n_positions = len(self._spread._positions)
        self._detail_visible = False
        self._last_preview_id: str | None = None
        self._deck_exit_started = False
        self._stream_thinking_text = ""
        self._stream_content_text = ""
        self._stream_queue: deque[StreamChunk] = deque()
        self._stream_timer: Timer | None = None
        self._stream_source_done = False
        self._stream_has_thinking = False
        self._stream_has_content = False

    def compose(self) -> ComposeResult:
        # Header
        with Vertical(id="draw-header"):
            yield Static(
                Text(f"✦ {self._spread.name_zh} ✦", style=f"bold {C_MAUVE}"),
                id="draw-title",
            )
            yield Static(
                Text(f'"{self._question}"', style=C_SUBTEXT0),
                id="draw-question",
            )
        yield Static("─── ✦ ───", id="draw-divider")

        # Deck
        with Vertical(id="deck-section"):
            yield Static("", id="deck-label")
            base_cards_per_row, extra_cards = divmod(NUM_DECK_CARDS, DECK_ROW_COUNT)
            card_index = 0
            with Vertical(id="deck-row"):
                for row_index in range(DECK_ROW_COUNT):
                    row_size = base_cards_per_row + int(row_index < extra_cards)
                    with Horizontal(classes="deck-row-line"):
                        for i in range(card_index, card_index + row_size):
                            yield DeckCard(i)
                    card_index += row_size

        # Main area: spread + detail panel
        with Horizontal(id="main-area"):
            with Vertical(id="spread-area"):
                yield Static("", id="spread-label")
                with Horizontal(id="spread-grid"):
                    for i, pos in enumerate(self._ordered_positions()):
                        yield SpreadSlot(i, pos.name_zh)

        with Vertical(id="card-preview"):
            yield Static("", id="preview-content")

        # Status + footer
        yield Static("", id="status")
        yield Static("", id="draw-footer")

        # Interpretation dialog (hidden until streaming starts)
        with VerticalScroll(id="interp-dialog"):
            yield Static("解读", id="interp-dialog-title")
            yield Static("", id="interp-dialog-content")
            yield Static("↑↓ 滚动  Q 关闭", id="interp-dialog-hints")

    def _ordered_positions(self) -> list:
        positions = self._spread._positions
        n = len(positions)
        if n == 5:
            idx = [4, 0, 1, 3, 2]
            return [positions[i] for i in idx]
        if n == 10:
            idx = [4, 0, 1, 5, 9, 3, 2, 6, 7, 8]
            return [positions[i] for i in idx]
        return list(positions)

    def _slot_for_position(self, position_index: int) -> SpreadSlot:
        slots = list(self.query(SpreadSlot))
        n = self._n_positions
        if n == 5:
            idx = [4, 0, 1, 3, 2]
            return slots[idx[position_index]]
        if n == 10:
            idx = [4, 0, 1, 5, 9, 3, 2, 6, 7, 8]
            return slots[idx[position_index]]
        return slots[position_index]

    def on_mount(self) -> None:
        self._prepare_drawn_cards()
        grid = self.query_one("#spread-grid")
        for cls in ("layout-1", "layout-3", "layout-5", "layout-10"):
            grid.remove_class(cls)
        grid.add_class(f"layout-{self._n_positions}")

        self._mark_waiting_slot()
        self._update_phase_ui()
        self._animate_deck_entrance()
        deck_cards = list(self.query(DeckCard))
        if deck_cards:
            deck_cards[0].focus()

    def _prepare_drawn_cards(self) -> None:
        if self._planned_cards:
            return
        for position in self._spread._positions:
            card, is_reversed = self._deck.draw(self.app.reversal_prob)
            self._planned_cards.append(
                DrawnCard(card=card, position=position, is_reversed=is_reversed)
            )

    def _mark_waiting_slot(self) -> None:
        for slot in self.query(SpreadSlot):
            slot.remove_class("waiting")
        if self._phase == Phase.PICK and self._pick_index < self._n_positions:
            slot = self._slot_for_position(self._pick_index)
            slot.add_class("waiting")

    def on_unmount(self) -> None:
        self._cancelled = True
        self._stop_stream_timer()

    def _hide_deck(self) -> None:
        try:
            self.query_one("#deck-section").display = False
            self._animate_spread_recenter()
        except Exception:
            pass

    def _animate_spread_recenter(self) -> None:
        main_area = self.query_one("#main-area")
        main_area.styles.offset = (0, SPREAD_RECENTER_OFFSET)
        if not self.app.animation_enabled:
            main_area.styles.offset = (0, 0)
            return
        main_area.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, 0)),
            duration=SPREAD_RECENTER_DURATION,
            easing=_EASE,
        )

    def _animate_deck_exit(self) -> None:
        deck_section = self.query_one("#deck-section")
        deck_section.styles.opacity = 0
        deck_section.styles.offset = (0, -2)
        for i, card in enumerate(c for c in self.query(DeckCard) if not c.has_class("picked")):
            self.set_timer(0.01 + i * 0.008, lambda c=card: c.add_class("exiting"))
        self.set_timer(DECK_HIDE_DELAY, self._hide_deck)

    # ── Phase UI ──────────────────────────────────────────────────────

    def _update_phase_ui(self) -> None:
        deck_label = self.query_one("#deck-label", Static)
        spread_label = self.query_one("#spread-label", Static)
        footer = self.query_one("#draw-footer", Static)
        deck_section = self.query_one("#deck-section")

        if self._phase == Phase.PICK:
            self._deck_exit_started = False
            deck_section.styles.opacity = 1.0
            deck_section.styles.offset = (0, 0)
            remaining = self._n_positions - self._pick_index
            if self._pick_index < self._n_positions:
                pos_name = self._spread._positions[self._pick_index].name_zh
                spread_label.update(
                    Text(f"── 牌阵 · 还需选 {remaining} 张 · 下一个: {pos_name} ──", style=f"bold {C_LAVENDER}")
                )
            else:
                spread_label.update(
                    Text("── 牌阵 · 选牌完成 ──", style=f"bold {C_LAVENDER}")
                )
            deck_label.update(
                Text(f"── 选牌 ({self._pick_index}/{self._n_positions}) ──", style=f"bold {C_LAVENDER}")
            )
            footer.update(Text("← → 选牌  Enter 抽牌", style=C_OVERLAY0))
            deck_section.display = True
        elif self._phase == Phase.FLIP:
            if not self._deck_exit_started:
                self._deck_exit_started = True
                self._animate_deck_exit()
            unrevealed = sum(1 for s in self.query(SpreadSlot) if not s.is_revealed)
            spread_label.update(
                Text(f"── 翻牌 · 剩余 {unrevealed} 张 ──", style=f"bold {C_LAVENDER}")
            )
            footer.update(Text("← → 选择  Enter 翻牌", style=C_OVERLAY0))
        elif self._phase == Phase.DONE:
            deck_section.display = False
            spread_label.update(
                Text("── ✦ 牌阵已就绪 ✦ ──", style=f"bold {C_LAVENDER}")
            )
            d_hint = "D 隐藏详情" if self._detail_visible else "D 详情"
            footer.update(Text(f"← → 选牌  {d_hint}  I 解读  Q 返回", style=C_OVERLAY0))

    # ── Deck entrance animation ──────────────────────────────────────

    def _animate_deck_entrance(self) -> None:
        if not self.app.animation_enabled:
            return
        for i, card in enumerate(self.query(DeckCard)):
            card.styles.opacity = 0
            card.styles.offset = (0, 1)
            self.set_timer(0.01 + i * 0.025, lambda c=card: self._reveal_deck_card(c))

    @staticmethod
    def _reveal_deck_card(card: DeckCard) -> None:
        card.styles.animate("opacity", 1.0, duration=0.32, easing=_EASE)
        card.styles.offset = (0, 0)

    # ── Spread slot entrance animation ────────────────────────────────

    def _animate_slot_entrance(self, slot: SpreadSlot, delay: float = 0.0) -> None:
        if not self.app.animation_enabled:
            return
        slot.styles.opacity = 0
        slot.styles.offset = (0, -SLOT_PLACE_OFFSET)
        self.set_timer(delay, lambda: self._reveal_slot(slot))

    @staticmethod
    def _reveal_slot(slot: SpreadSlot) -> None:
        slot.styles.animate("opacity", 1.0, duration=SLOT_PLACE_DURATION, easing=_EASE)
        slot.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, 0)),
            duration=SLOT_PLACE_DURATION,
            easing=_EASE,
        )

    # ── Pick phase ────────────────────────────────────────────────────

    async def on_deck_card_picked(self, event: DeckCard.Picked) -> None:
        if self._phase != Phase.PICK:
            return
        event.stop()

        card_widget = event.card
        if card_widget.has_class("picked"):
            return
        if self._pick_index >= len(self._planned_cards):
            return
        dc = self._planned_cards[self._pick_index]
        self._drawn_cards.append(dc)

        card_widget.add_class("picked")

        slot = self._slot_for_position(self._pick_index)
        slot.place_card(dc)
        self._animate_slot_entrance(slot, delay=0.08)

        self._pick_index += 1
        self._mark_waiting_slot()
        self._update_phase_ui()

        if self._pick_index >= self._n_positions:
            await asyncio.sleep(PICK_COMPLETE_DELAY)
            self._phase = Phase.FLIP
            self._update_phase_ui()
            unrevealed = [s for s in self.query(SpreadSlot) if not s.is_revealed]
            if unrevealed:
                unrevealed[0].focus()

    # ── Flip phase ────────────────────────────────────────────────────

    async def on_spread_slot_flipped(self, event: SpreadSlot.Flipped) -> None:
        if self._phase != Phase.FLIP:
            return
        event.stop()
        await event.slot.flip()
        self._update_phase_ui()

        slots = list(self.query(SpreadSlot))
        if all(s.is_revealed for s in slots):
            if self.app.animation_enabled:
                self.run_worker(self._completion_shimmer(slots), exclusive=False)
            self._phase = Phase.DONE
            self._show_detail_panel(slots[0] if slots else None)
            self._update_phase_ui()
            slots[0].focus()

    async def on_spread_slot_selected(self, event: SpreadSlot.Selected) -> None:
        """Update detail panel when a revealed card is focused."""
        if self._phase != Phase.DONE:
            return
        event.stop()
        self._update_detail(event.slot)

    async def _completion_shimmer(self, slots: list[SpreadSlot]) -> None:
        if not self.app.animation_enabled:
            return
        for i, slot in enumerate(slots):
            self.set_timer(0.01 + i * 0.08, lambda s=slot: self._pulse_slot(s))
        await asyncio.sleep(len(slots) * 0.08 + 0.22)

    @staticmethod
    def _pulse_slot(slot: SpreadSlot) -> None:
        slot.add_class("glow")
        slot.set_timer(0.22, lambda: slot.remove_class("glow"))

    # ── Detail panel ──────────────────────────────────────────────────

    def _show_detail_panel(self, slot: SpreadSlot | None = None) -> None:
        self._detail_visible = True
        self._sync_interp_layout()
        preview = self.query_one("#card-preview")
        preview.display = True
        if self.app.animation_enabled:
            preview.styles.opacity = 0
            preview.styles.offset = (4, 0)
        preview.add_class("visible")
        if self.app.animation_enabled:
            preview.styles.animate("opacity", 1.0, duration=0.24, easing=_EASE)
            preview.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 0)),
                duration=0.32,
                easing=_EASE,
            )
        self._last_preview_id = None
        if slot is not None:
            self._update_detail(slot)

    def _hide_detail_panel(self) -> None:
        self._detail_visible = False
        self._sync_interp_layout()
        self._center_spread_area()
        preview = self.query_one("#card-preview")
        if self.app.animation_enabled:
            preview.styles.animate("opacity", 0.0, duration=0.18, easing=_EASE)
            preview.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(4, 0)),
                duration=0.24,
                easing=_EASE,
            )
            self.set_timer(0.24, self._finish_hide_detail_panel)
        else:
            self._finish_hide_detail_panel()

    def _finish_hide_detail_panel(self) -> None:
        preview = self.query_one("#card-preview")
        preview.remove_class("visible")
        preview.display = False
        self._center_spread_area()

    def action_toggle_detail(self) -> None:
        if self._phase != Phase.DONE:
            return
        if self._detail_visible:
            self._hide_detail_panel()
        else:
            self._show_detail_panel()
            slots = list(self.query(SpreadSlot))
            if slots:
                self._update_detail(slots[0])
                slots[0].focus()
        self._update_phase_ui()

    def _update_detail(self, slot: SpreadSlot) -> None:
        if not self._detail_visible or not slot.drawn_card:
            return
        dc = slot.drawn_card
        preview_id = f"{dc.card.id}:{dc.is_reversed}"
        if self._last_preview_id == preview_id:
            return
        self._last_preview_id = preview_id

        content = self.query_one("#preview-content", Static)
        if self.app.render_mode != "text":
            img_detail = render_card_image_detail(dc)
            if img_detail:
                content.update(img_detail)
                return
        content.update(render_card_detail(dc))

    # ── Interpretation ────────────────────────────────────────────────

    def _sync_interp_layout(self) -> None:
        try:
            dialog = self.query_one("#interp-dialog")
        except NoMatches:
            return
        if self._detail_visible:
            dialog.add_class("detail-visible")
            dialog.styles.width = max(
                40,
                self.size.width
                - DETAIL_PANEL_WIDTH
                - INTERP_SIDE_MARGIN
                - INTERP_DETAIL_GAP,
            )
        else:
            dialog.remove_class("detail-visible")
            dialog.styles.width = max(
                40,
                self.size.width
                - INTERP_FULL_SIDE_MARGIN * 2
                + INTERP_FULL_WIDTH_CORRECTION,
            )

    def _center_spread_area(self) -> None:
        main_area = self.query_one("#main-area")
        if self.app.animation_enabled:
            main_area.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 0)),
                duration=0.22,
                easing=_EASE,
            )
        else:
            main_area.styles.offset = (0, 0)

    def action_interpret(self) -> None:
        if self._phase == Phase.DONE and not self._interp_streaming:
            self._do_interpret()

    def action_handle_back(self) -> None:
        if self.query_one("#interp-dialog").has_class("visible"):
            self.app.push_screen(
                ConfirmExitInterpretation(),
                callback=self._on_exit_interpretation_confirmed,
            )
        else:
            go_home(self)

    def _on_exit_interpretation_confirmed(self, confirmed: bool) -> None:
        if not confirmed:
            return
        self._cancelled = True
        self._stop_stream_timer()
        go_home(self)

    def _do_interpret(self) -> None:
        self._cancelled = False
        self._show_interp_dialog()
        self.run_worker(self._run_interpretation(), exclusive=True)

    def _show_interp_dialog(self) -> None:
        self._interp_streaming = True
        dialog = self.query_one("#interp-dialog")
        self._sync_interp_layout()
        dialog.display = True
        if self.app.animation_enabled:
            dialog.styles.opacity = 0
            dialog.styles.offset = (0, 2)
        dialog.add_class("visible")
        if self.app.animation_enabled:
            dialog.styles.animate("opacity", 1.0, duration=0.24, easing=_EASE)
            dialog.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 0)),
                duration=0.32,
                easing=_EASE,
            )
        self._reset_stream_display()
        self.query_one("#status", Static).update("")
        self.query_one("#draw-footer", Static).update(
            Text("Q 取消", style=C_OVERLAY0)
        )

    def on_resize(self) -> None:
        self._sync_interp_layout()

    def _hide_interp_dialog(self) -> None:
        self._interp_streaming = False
        self._stop_stream_timer()
        dialog = self.query_one("#interp-dialog")
        if self.app.animation_enabled:
            dialog.styles.animate("opacity", 0.0, duration=0.18, easing=_EASE)
            dialog.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 2)),
                duration=0.24,
                easing=_EASE,
            )
            self.set_timer(0.24, lambda: dialog.remove_class("visible"))
        else:
            dialog.remove_class("visible")
        self._update_phase_ui()

    def _show_error(self, message: str) -> None:
        self._hide_interp_dialog()
        self.query_one("#status", Static).update(Text(message, style=C_RED))

    def _reset_stream_display(self) -> None:
        self._stream_thinking_text = ""
        self._stream_content_text = ""
        self._stream_queue.clear()
        self._stream_source_done = False
        self._stream_has_thinking = False
        self._stream_has_content = False
        self._render_stream_content()
        self.query_one("#interp-dialog-hints", Static).update(
            Text("模型正在解读...  ↑↓ 滚动", style=C_OVERLAY0)
        )

    def _stop_stream_timer(self) -> None:
        if self._stream_timer is not None:
            self._stream_timer.stop()
            self._stream_timer = None
        self._stream_queue.clear()

    def _append_stream_chunk(self, chunk: StreamChunk) -> None:
        if not chunk.text:
            return
        self._stream_queue.append(chunk)
        if self._stream_timer is None:
            self._stream_timer = self.set_interval(
                STREAM_TYPE_INTERVAL, self._type_stream_tick
            )

    def _type_stream_tick(self) -> None:
        if not self._stream_queue:
            if self._stream_source_done:
                self._finish_stream_display()
                return
            self._stop_stream_timer()
            return

        for _ in range(STREAM_CHARS_PER_TICK):
            if not self._stream_queue:
                break
            chunk = self._stream_queue[0]
            if not chunk.text:
                self._stream_queue.popleft()
                continue
            self._append_stream_text(chunk.kind, chunk.text[0])
            rest = chunk.text[1:]
            if rest:
                self._stream_queue[0] = StreamChunk(rest, chunk.kind)
            else:
                self._stream_queue.popleft()

        self._render_stream_content()
        self._scroll_interp_to_bottom()

    def _append_stream_text(self, kind: str, text: str) -> None:
        if kind == "thinking":
            self._stream_thinking_text += text
            self._stream_has_thinking = True
        else:
            self._stream_content_text += text
            self._stream_has_content = True

    def _render_stream_content(self) -> None:
        parts = []
        if self._stream_thinking_text:
            parts.append(Text("思考", style=f"bold {C_SUBTEXT0}"))
            parts.append(Markdown(self._stream_thinking_text, style=C_SUBTEXT0))
        if self._stream_content_text:
            if parts:
                parts.append(Text(""))
            parts.append(Text("解读", style=f"bold {C_MAUVE}"))
            parts.append(Markdown(self._stream_content_text, style=C_TEXT))
        self.query_one("#interp-dialog-content", Static).update(Group(*parts))

    def _scroll_interp_to_bottom(self) -> None:
        try:
            self.query_one("#interp-dialog", VerticalScroll).scroll_end(animate=False)
        except NoMatches:
            pass

    def _stream_done(self) -> None:
        self._stream_source_done = True
        if self._stream_queue and self._stream_timer is None:
            self._stream_timer = self.set_interval(
                STREAM_TYPE_INTERVAL, self._type_stream_tick
            )
            return
        if not self._stream_queue:
            self._finish_stream_display()

    def _finish_stream_display(self) -> None:
        self._stop_stream_timer()
        self._interp_streaming = False
        self.query_one("#interp-dialog-hints", Static).update(
            Text("── 完成 ──  ↑↓ 滚动  Q 关闭", style=C_OVERLAY0)
        )

    async def _run_interpretation(self) -> None:
        try:
            config = self.app.config
            interp = get_interpreter(config)
            loop = asyncio.get_running_loop()

            def _consume_stream():
                for chunk in interp.interpret_stream(self._drawn_cards, self._question):
                    if self._cancelled:
                        return
                    if isinstance(chunk, str):
                        chunk = StreamChunk(chunk, "content")
                    self.app.call_from_thread(self._append_stream_chunk, chunk)

            await loop.run_in_executor(None, _consume_stream)
        except InterpretationError as exc:
            if not self.is_mounted or self._cancelled:
                return
            self._show_error(f"解读失败: {exc}")
            return
        except Exception as exc:
            if not self.is_mounted or self._cancelled:
                return
            msg = str(exc)
            if "api_key" in msg.lower() or "unauthorized" in msg.lower():
                self._show_error("API key 未配置，请在 .neko/settings.json 中设置 api_key")
            else:
                self._show_error(f"解读失败: {exc}")
            return
        if not self.is_mounted or self._cancelled:
            return
        self._stream_done()

    # ── Focus navigation ──────────────────────────────────────────────

    def key_left(self) -> None:
        self._focus_neighbor("left")

    def key_right(self) -> None:
        self._focus_neighbor("right")

    def key_up(self) -> None:
        if self._interp_is_visible():
            self.query_one("#interp-dialog", VerticalScroll).scroll_up(animate=True)
            return
        self._focus_neighbor("up")

    def key_down(self) -> None:
        if self._interp_is_visible():
            self.query_one("#interp-dialog", VerticalScroll).scroll_down(animate=True)
            return
        self._focus_neighbor("down")

    def key_tab(self, event: Key) -> None:
        event.stop()
        self._focus_neighbor("right")

    def _interp_is_visible(self) -> bool:
        return self.query_one("#interp-dialog").has_class("visible")

    def _focus_neighbor(self, direction: str) -> None:
        if self._phase == Phase.PICK:
            widgets = list(self.query(DeckCard))
            row_width = NUM_DECK_CARDS // DECK_ROW_COUNT
        elif self._phase == Phase.FLIP:
            widgets = [s for s in self.query(SpreadSlot) if not s.is_revealed]
            row_width = self._spread_row_width(len(widgets))
        else:
            widgets = list(self.query(SpreadSlot))
            row_width = self._spread_row_width(len(widgets))
        if not widgets:
            return
        try:
            idx = widgets.index(self.focused)
        except ValueError:
            widgets[0].focus()
            return
        delta = self._direction_delta(direction, row_width)
        new_idx = idx + delta
        if 0 <= new_idx < len(widgets):
            widgets[new_idx].focus()

    @staticmethod
    def _direction_delta(direction: str, row_width: int) -> int:
        if direction == "left":
            return -1
        if direction == "right":
            return 1
        if direction == "up":
            return -row_width
        if direction == "down":
            return row_width
        return 0

    @staticmethod
    def _spread_row_width(count: int) -> int:
        if count >= 5:
            return 3
        return 1
