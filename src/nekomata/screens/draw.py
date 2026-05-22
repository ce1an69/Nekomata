"""Draw screen — pick cards from a face-down deck, then flip to reveal."""

import asyncio
from enum import Enum, auto

from rich.text import Text

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.css.scalar import ScalarOffset
from textual.css.query import NoMatches
from textual.events import DescendantFocus, Key, Resize
from textual.geometry import Offset
from textual.screen import Screen
from textual.widgets import Static

from nekomata.card.deck import Deck
from nekomata.card.types import DrawnCard
from nekomata.render.card_renderer import (
    render_card_detail,
    render_card_full_detail,
)
from nekomata.render.styles import (
    C_CRUST,
    C_LAVENDER,
    C_MANTLE,
    C_MAUVE,
    C_OVERLAY0,
    C_PINK,
    C_RED,
    C_SUBTEXT0,
    C_SURFACE0,
    C_SURFACE1,
    C_SURFACE2,
    C_TEXT,
    EASE,
)
from nekomata.screens.box_manager import BoxManager
from nekomata.screens.draw_widgets import (
    DECK_CARD_WIDTH,
    DECK_HIDE_DELAY,
    DECK_ROW_COUNT,
    NUM_DECK_CARDS,
    PICK_COMPLETE_DELAY,
    SLOT_PLACE_DURATION,
    SLOT_PLACE_OFFSET,
    SPREAD_RECENTER_DURATION,
    SPREAD_RECENTER_OFFSET,
    ConfirmExitInterpretation,
    DeckCard,
    SpreadSlot,
)
from nekomata.screens.stream_handler import StreamHandler
from nekomata.screens.widgets import go_home
from nekomata.spread import get_spread

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
        transition: opacity 420ms {EASE}, offset 420ms {EASE}, border 180ms {EASE};
    }}
    #deck-section.box-active {{
        border-bottom: tall {C_MAUVE};
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
        transition: offset 280ms {EASE};
    }}
    #spread-area {{
        width: 1fr;
        height: 1fr;
        padding: 1 0;
        align: center middle;
        border: round transparent;
        transition: border 180ms {EASE};
    }}
    #spread-area.box-active {{
        border: round {C_MAUVE};
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
        grid-columns: 20;
    }}
    #spread-grid.layout-3 {{
        layout: grid;
        grid-size: 3 1;
        grid-columns: 20 20 20;
    }}
    #spread-grid.layout-5 {{
        layout: grid;
        grid-size: 3 2;
        grid-columns: 20 20 20;
        grid-rows: 1fr 1fr;
    }}
    #spread-grid.layout-10 {{
        layout: grid;
        grid-size: 5 2;
        grid-columns: 20 20 20 20 20;
        grid-rows: 1fr 1fr;
    }}
    #card-preview {{
        dock: right;
        width: {DETAIL_PANEL_WIDTH};
        min-width: {DETAIL_PANEL_WIDTH};
        height: 1fr;
        border: round {C_SURFACE0};
        background: {C_MANTLE};
        padding: 1 1;
        opacity: 0;
        display: none;
        offset: 4 0;
        transition: opacity 240ms {EASE}, offset 320ms {EASE}, border 180ms {EASE};
    }}
    #card-preview.box-active {{
        border: round {C_MAUVE};
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
        border: round {C_SURFACE1};
        background: {C_MANTLE};
        padding: 0 1;
        margin: 0 1 1 1;
        opacity: 0;
        offset: 0 2;
        transition: opacity 240ms {EASE}, offset 320ms {EASE}, width 220ms {EASE}, border 180ms {EASE};
    }}
    #interp-dialog.box-active {{
        border: round {C_MAUVE};
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
        self._n_positions = len(self._spread.positions)
        self._detail_visible = False
        self._last_preview_id: str | None = None
        self._deck_exit_started = False
        self._display_order = self._spread.display_order
        self._ordered_positions = [self._spread.positions[i] for i in self._display_order]

        self._box = BoxManager(self, self._available_boxes)
        self._stream = StreamHandler(
            screen=self,
            render_content=self._on_stream_render,
            render_hints=self._on_stream_hints,
            scroll_to_bottom=self._on_stream_scroll,
            show_error=self._show_error,
        )

    # ── Callbacks for StreamHandler ──────────────────────────────────

    def _on_stream_render(self, parts) -> None:
        content = self.query_one("#interp-dialog-content", Static)
        if parts is None:
            content.update("")
        else:
            from rich.console import Group
            content.update(Group(*parts))

    def _on_stream_hints(self, text) -> None:
        self.query_one("#interp-dialog-hints", Static).update(text)

    def _on_stream_scroll(self) -> None:
        try:
            self.query_one("#interp-dialog", VerticalScroll).scroll_end(animate=False)
        except NoMatches:
            pass

    # ── Delegation to StreamHandler (for test compatibility) ─────────

    def _append_stream_chunk(self, chunk) -> None:
        self._stream.append_chunk(chunk)

    @property
    def _loading_timer(self):
        return self._stream._loading_timer

    @property
    def _stream_timer(self):
        return self._stream._timer

    # ── Box available_boxes callback ─────────────────────────────────

    def _available_boxes(self) -> list[str]:
        if self._phase == Phase.PICK:
            return ["deck"]
        if self._phase == Phase.FLIP:
            return ["spread"]
        boxes = ["spread"]
        if self._detail_visible:
            boxes.append("detail")
        if self._interp_is_visible():
            boxes.append("interp")
        return boxes

    def _interp_is_visible(self) -> bool:
        return self.query_one("#interp-dialog").has_class("visible")

    # ── Compose ──────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Vertical(id="draw-header"):
            yield Static(
                Text(f"✦ {self._spread.name} ✦", style=f"bold {C_MAUVE}"),
                id="draw-title",
            )
            yield Static(
                Text(f'"{self._question}"', style=C_SUBTEXT0),
                id="draw-question",
            )
        yield Static("─── ✦ ───", id="draw-divider")

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

        with Horizontal(id="main-area"):
            with Vertical(id="spread-area"):
                yield Static("", id="spread-label")
                with Horizontal(id="spread-grid"):
                    for i, pos in enumerate(self._ordered_positions):
                        yield SpreadSlot(i, pos.name)

        with VerticalScroll(id="card-preview"):
            yield Static("", id="preview-content")

        yield Static("", id="status")
        yield Static("", id="draw-footer")

        with VerticalScroll(id="interp-dialog"):
            yield Static("解读", id="interp-dialog-title")
            yield Static("", id="interp-dialog-content")
            yield Static("Q 关闭", id="interp-dialog-hints")

    def _slot_for_position(self, position_index: int) -> SpreadSlot:
        slots = list(self.query(SpreadSlot))
        return slots[self._display_order[position_index]]

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
        self._box.active_box = "deck"
        self._box.update_highlights()

    def _prepare_drawn_cards(self) -> None:
        if self._planned_cards:
            return
        for position in self._spread.positions:
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
        self._stream.stop()

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
            easing=EASE,
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
                pos_name = self._spread.positions[self._pick_index].name
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
        card.styles.animate("opacity", 1.0, duration=0.32, easing=EASE)
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
        slot.styles.animate("opacity", 1.0, duration=SLOT_PLACE_DURATION, easing=EASE)
        slot.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, 0)),
            duration=SLOT_PLACE_DURATION,
            easing=EASE,
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
            self._box.active_box = "spread"
            self._box.update_highlights()
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
            self._box.active_box = "spread"
            self._box.update_highlights()
            self._show_detail_panel(slots[0] if slots else None)
            self._update_phase_ui()
            for s in slots:
                s.remove_class("selected")
            slots[0].add_class("selected")
            slots[0].focus()
        else:
            unrevealed = [s for s in slots if not s.is_revealed]
            if unrevealed:
                unrevealed[0].focus()

    async def on_spread_slot_selected(self, event: SpreadSlot.Selected) -> None:
        if self._phase != Phase.DONE:
            return
        event.stop()
        for s in self.query(SpreadSlot):
            s.remove_class("selected")
        event.slot.add_class("selected")
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
        self._fit_detail_panel_height()
        self.call_after_refresh(self._fit_detail_panel_height)
        if self.app.animation_enabled:
            preview.styles.opacity = 0
            preview.styles.offset = (4, 0)
        preview.add_class("visible")
        if self.app.animation_enabled:
            preview.styles.animate("opacity", 1.0, duration=0.24, easing=EASE)
            preview.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 0)),
                duration=0.32,
                easing=EASE,
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
            preview.styles.animate("opacity", 0.0, duration=0.18, easing=EASE)
            preview.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(4, 0)),
                duration=0.24,
                easing=EASE,
            )
            self.set_timer(0.24, self._finish_hide_detail_panel)
        else:
            self._finish_hide_detail_panel()

    def _finish_hide_detail_panel(self) -> None:
        preview = self.query_one("#card-preview")
        preview.remove_class("visible")
        preview.display = False
        preview.styles.height = "1fr"
        self._center_spread_area()

    def _fit_detail_panel_height(self) -> None:
        try:
            preview = self.query_one("#card-preview")
            main_area = self.query_one("#main-area")
        except NoMatches:
            return
        bottom = main_area.region.y + main_area.region.height
        try:
            dialog = self.query_one("#interp-dialog")
        except NoMatches:
            pass
        else:
            if dialog.has_class("visible"):
                bottom = max(bottom, dialog.region.y + dialog.region.height)
        preview.styles.height = max(1, bottom - 1)

    def action_toggle_detail(self) -> None:
        if self._phase != Phase.DONE:
            return
        if self._detail_visible:
            if self._box.active_box == "detail":
                self._box.active_box = "spread"
                self._box.update_highlights()
                self._box.focus_widget()
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
            full_detail = render_card_full_detail(dc)
            if full_detail:
                content.update(full_detail)
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
            dialog.styles.margin = (0, 1, 2, 1)
            dialog.styles.width = max(
                40,
                self.size.width
                - DETAIL_PANEL_WIDTH
                - INTERP_SIDE_MARGIN
                - INTERP_DETAIL_GAP,
            )
        else:
            dialog.remove_class("detail-visible")
            dialog.styles.margin = (0, 1, 1, 1)
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
                easing=EASE,
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
        self._stream.stop()
        go_home(self)

    def _do_interpret(self) -> None:
        self._cancelled = False
        self._show_interp_dialog()
        self.run_worker(
            self._stream.run(self._drawn_cards, self._question, lambda: self._cancelled),
            exclusive=True,
        )

    def _show_interp_dialog(self) -> None:
        self._interp_streaming = True
        dialog = self.query_one("#interp-dialog")
        self._box.active_box = "interp"
        self._box.update_highlights()
        self._sync_interp_layout()
        self._fit_detail_panel_height()
        dialog.display = True
        if self.app.animation_enabled:
            dialog.styles.opacity = 0
            dialog.styles.offset = (0, 2)
        dialog.add_class("visible")
        if self.app.animation_enabled:
            dialog.styles.animate("opacity", 1.0, duration=0.24, easing=EASE)
            dialog.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 0)),
                duration=0.32,
                easing=EASE,
            )
        self._stream.reset()
        self.query_one("#status", Static).update("")

    def on_resize(self, event: Resize) -> None:
        self._fit_detail_panel_height()
        self._sync_interp_layout()

    def _hide_interp_dialog(self) -> None:
        self._interp_streaming = False
        self._stream.stop()
        self._box.active_box = "spread"
        self._box.update_highlights()
        self._sync_interp_layout()
        self._fit_detail_panel_height()
        dialog = self.query_one("#interp-dialog")
        if self.app.animation_enabled:
            dialog.styles.animate("opacity", 0.0, duration=0.18, easing=EASE)
            dialog.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 2)),
                duration=0.24,
                easing=EASE,
            )
            self.set_timer(0.24, lambda: dialog.remove_class("visible"))
        else:
            dialog.remove_class("visible")
        self._update_phase_ui()

    def _show_error(self, message: str) -> None:
        self._hide_interp_dialog()
        self.query_one("#status", Static).update(Text(message, style=C_RED))

    # ── Focus navigation ──────────────────────────────────────────────

    def on_key(self, event: Key) -> None:
        if event.key == "shift+tab":
            event.stop()
            self._box.cycle(-1)

    def key_tab(self, event: Key) -> None:
        event.stop()
        self._box.cycle(1)

    def key_left(self) -> None:
        if self._box.active_box in ("detail", "interp"):
            return
        self._box.focus_neighbor("left", self._phase, self._n_positions)

    def key_right(self) -> None:
        if self._box.active_box in ("detail", "interp"):
            return
        self._box.focus_neighbor("right", self._phase, self._n_positions)

    def key_up(self) -> None:
        if self._box.active_box == "interp":
            self.query_one("#interp-dialog", VerticalScroll).scroll_up(animate=True)
        elif self._box.active_box == "detail":
            self.query_one("#card-preview", VerticalScroll).scroll_up(animate=True)
        else:
            self._box.focus_neighbor("up", self._phase, self._n_positions)

    def key_down(self) -> None:
        if self._box.active_box == "interp":
            self.query_one("#interp-dialog", VerticalScroll).scroll_down(animate=True)
        elif self._box.active_box == "detail":
            self.query_one("#card-preview", VerticalScroll).scroll_down(animate=True)
        else:
            self._box.focus_neighbor("down", self._phase, self._n_positions)

    def on_descendant_focus(self, event: DescendantFocus) -> None:
        self._box.on_focus_change(event.widget)
