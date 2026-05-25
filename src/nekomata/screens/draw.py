"""Draw screen — pick cards from a face-down deck, then flip to reveal."""

import asyncio
from enum import Enum, auto

from rich.console import Group
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
from nekomata.render.card_renderer import clear_cache, preload_all_async, preload_card_image_async
from nekomata.render.styles import C_LAVENDER, C_MAUVE, C_OVERLAY0, C_SUBTEXT0, C_TEXT, EASE, EASE_SPRING
from nekomata.screens.box_manager import BoxManager
from nekomata.screens.draw_css import DRAW_SCREEN_CSS
from nekomata.screens.draw_dialog import InterpretationDialog
from nekomata.screens.draw_detail import DetailPanel
from nekomata.screens.draw_widgets import (
    DECK_ENTRANCE_FADE, DECK_ENTRANCE_STAGGER,
    DECK_HIDE_DELAY, DECK_ROW_COUNT, NUM_DECK_CARDS, PICK_COMPLETE_DELAY,
    SPREAD_SLOT_ENTRANCE_FADE, SPREAD_SLOT_ENTRANCE_STAGGER,
    SLOT_PLACE_DURATION, SLOT_PLACE_OFFSET, SPREAD_RECENTER_DURATION, SPREAD_RECENTER_OFFSET,
    ConfirmExitInterpretation, DeckCard, SpreadSlot,
)
from nekomata.screens.stream_handler import StreamHandler
from nekomata.screens.widgets import go_home
from nekomata.i18n import lazy_section
from nekomata.strings import ORNAMENT
from nekomata.spread import get_spread

_STR = lazy_section("draw")


class Phase(Enum):
    """Draw screen state machine: PICK → FLIP → DONE."""
    PICK = auto()   # User selecting cards from the deck
    FLIP = auto()   # All cards placed, user flipping to reveal
    DONE = auto()   # All cards revealed, detail + interpretation available


class DrawScreen(Screen):
    """Card drawing screen: pick from deck → flip to reveal → detail + interpret."""

    BINDINGS = [
        Binding("q", "handle_back", "Back"),
        Binding("escape", "handle_back", "Back"),
        Binding("i", "interpret", "Interpret", show=False),
        Binding("d", "toggle_detail", "Detail", show=False),
    ]

    DEFAULT_CSS = DRAW_SCREEN_CSS

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
        self._dealing = False
        self._n_positions = len(self._spread.positions)
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
            show_error=self._on_stream_error,
        )
        self._dialog = InterpretationDialog(self, self._box, self._stream)
        self._detail = DetailPanel(self)

    # -- StreamHandler callbacks --

    def _on_stream_render(self, parts) -> None:
        if parts is None:
            self._w_interp_content.update("")
        else:
            self._w_interp_content.update(Group(*parts))

    def _on_stream_hints(self, text) -> None:
        self._w_interp_hints.update(text)

    def _on_stream_scroll(self) -> None:
        try:
            self._w_interp.scroll_end(animate=False)
        except NoMatches:
            pass  # Widget may not be mounted yet during early streaming

    def _on_stream_error(self, message: str) -> None:
        self._dialog.show_error(
            message,
            self._update_phase_ui,
            sync_layout=self._sync_interp_layout,
            fit_height=lambda: self._dialog.fit_height(self._w_main_area, self._detail.visible),
        )

    # Exposed for integration tests (test_flow.py)
    @property
    def _loading_timer(self):
        return self._stream._loading_timer

    @property
    def _stream_timer(self):
        return self._stream._timer

    # -- BoxManager callback --

    def _available_boxes(self) -> list[str]:
        if self._phase == Phase.PICK:
            return ["deck"]
        if self._phase == Phase.FLIP:
            return ["spread"]
        boxes = ["spread"]
        if self._detail.visible:
            boxes.append("detail")
        if self._dialog.is_visible:
            boxes.append("interp")
        return boxes

    # -- Compose --

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
        yield Static(ORNAMENT, id="draw-divider")

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
            pass

        yield Static("", id="status")
        yield Static("", id="draw-footer")

        with VerticalScroll(id="interp-dialog"):
            yield Static(_STR["interp_title"], id="interp-dialog-title")
            yield Static("", id="interp-dialog-content")
            yield Static(_STR["interp_close_hint"], id="interp-dialog-hints")

    # -- Mount / Unmount --

    def on_mount(self) -> None:
        self._prepare_drawn_cards()

        # Cache widget references
        self._w_deck_section = self.query_one("#deck-section")
        self._w_deck_label = self.query_one("#deck-label", Static)
        self._w_main_area = self.query_one("#main-area")
        self._w_spread_label = self.query_one("#spread-label", Static)
        self._w_spread_grid = self.query_one("#spread-grid")
        self._w_interp = self.query_one("#interp-dialog")
        self._w_interp_content = self.query_one("#interp-dialog-content", Static)
        self._w_interp_hints = self.query_one("#interp-dialog-hints", Static)
        self._w_footer = self.query_one("#draw-footer", Static)

        self._dialog.cache_widgets()
        self._detail.cache_widgets()

        grid = self._w_spread_grid
        for cls in ("layout-1", "layout-3", "layout-5", "layout-10"):
            grid.remove_class(cls)
        grid.add_class(f"layout-{self._n_positions}")

        self._w_main_area.display = False
        self._update_phase_ui()
        self._animate_deck_entrance()
        if not self._dealing:
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

    def on_unmount(self) -> None:
        self._cancelled = True
        self._stream.stop()
        clear_cache()

    # -- Deck animation --

    def _hide_deck(self) -> None:
        self._w_deck_section.display = False
        self._animate_spread_recenter()

    def _animate_spread_recenter(self) -> None:
        self._w_main_area.styles.offset = (0, SPREAD_RECENTER_OFFSET)
        if not self.app.animation_enabled:
            self._w_main_area.styles.offset = (0, 0)
            return
        self._w_main_area.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, 0)),
            duration=SPREAD_RECENTER_DURATION,
            easing=EASE,
        )

    def _animate_deck_exit(self) -> None:
        self._w_deck_section.styles.opacity = 0
        self._w_deck_section.styles.offset = (0, -2)
        for i, card in enumerate(c for c in self.query(DeckCard) if not c.has_class("picked")):
            self.set_timer(0.01 + i * 0.008, lambda c=card: c.add_class("exiting"))
        self.set_timer(DECK_HIDE_DELAY, self._hide_deck)

    def _animate_deck_entrance(self) -> None:
        if not self.app.animation_enabled:
            return
        self._dealing = True
        cards = list(self.query(DeckCard))
        for i, card in enumerate(cards):
            card.styles.opacity = 0
            card.styles.offset = (0, 1)
            self.set_timer(
                0.01 + i * DECK_ENTRANCE_STAGGER,
                lambda c=card: self._reveal_deck_card(c),
            )
        total = 0.01 + len(cards) * DECK_ENTRANCE_STAGGER + DECK_ENTRANCE_FADE + 0.05
        self.set_timer(total, self._enable_deck_selection)

    @staticmethod
    def _reveal_deck_card(card: DeckCard) -> None:
        card.styles.animate("opacity", 1.0, duration=DECK_ENTRANCE_FADE, easing=EASE)
        card.styles.offset = (0, 0)

    def _enable_deck_selection(self) -> None:
        """Enable card selection after dealing animation completes."""
        self._dealing = False
        deck_cards = list(self.query(DeckCard))
        if deck_cards:
            deck_cards[0].focus()

    # -- Phase UI --

    def _update_phase_ui(self) -> None:
        """Update labels and footer hints to match the current phase."""
        lbl = f"bold {C_LAVENDER}"
        if self._phase == Phase.PICK:
            self._deck_exit_started = False
            self._w_deck_section.styles.opacity = 1.0
            self._w_deck_section.styles.offset = (0, 0)
            if self._pick_index < self._n_positions:
                pos_name = self._spread.positions[self._pick_index].name
                remaining = self._n_positions - self._pick_index
                spread_text = _STR["pick_next"].format(remaining=remaining, name=pos_name)
            else:
                spread_text = _STR["pick_done"]
            self._w_spread_label.update(Text(spread_text, style=lbl))
            self._w_deck_label.update(Text(
                _STR["pick_label"].format(picked=self._pick_index, total=self._n_positions), style=lbl
            ))
            self._w_footer.update(Text(_STR["hint_pick"], style=C_OVERLAY0))
            self._w_deck_section.display = True
        elif self._phase == Phase.FLIP:
            if not self._deck_exit_started:
                self._deck_exit_started = True
                self._animate_deck_exit()
            unrevealed = sum(1 for s in self.query(SpreadSlot) if not s.is_revealed)
            self._w_spread_label.update(Text(_STR["flip_label"].format(unrevealed=unrevealed), style=lbl))
            self._w_footer.update(Text(_STR["hint_flip"], style=C_OVERLAY0))
        elif self._phase == Phase.DONE:
            self._w_deck_section.display = False
            self._w_spread_label.update(Text(_STR["done_label"], style=lbl))
            d_hint = _STR["detail_hide"] if self._detail.visible else _STR["detail_show"]
            self._w_footer.update(Text(_STR["hint_done"].format(detail_hint=d_hint), style=C_OVERLAY0))

    # -- Pick phase --

    async def on_deck_card_picked(self, event: DeckCard.Picked) -> None:
        if self._phase != Phase.PICK or self._dealing:
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
        self.run_worker(preload_card_image_async(dc.card, dc.is_reversed), exclusive=False)

        self._pick_index += 1
        self._update_phase_ui()

        if self._pick_index >= self._n_positions:
            await asyncio.sleep(PICK_COMPLETE_DELAY)
            await self._reveal_spread()

    async def _reveal_spread(self) -> None:
        """Show spread area, ensure all images cached, then enter FLIP phase."""
        await preload_all_async(
            [(dc.card, dc.is_reversed) for dc in self._drawn_cards]
        )
        self._w_deck_section.display = False
        self._w_main_area.display = True

        slots = list(self.query(SpreadSlot))
        for i, dc in enumerate(self._drawn_cards):
            slots[self._display_order[i]].place_card(dc)

        self._deck_exit_started = True
        self._phase = Phase.FLIP
        self._box.active_box = "spread"
        self._box.update_highlights()
        self._update_phase_ui()

        # Focus first slot immediately so the UI stays responsive
        self._focus_first_slot()

        if self.app.animation_enabled:
            for slot in slots:
                slot.styles.opacity = 0
                slot.styles.offset = (0, 2)
            for i, slot in enumerate(slots):
                self.set_timer(
                    0.05 + i * SPREAD_SLOT_ENTRANCE_STAGGER,
                    lambda s=slot: self._animate_slot_entrance(s),
                )
            total = 0.05 + len(slots) * SPREAD_SLOT_ENTRANCE_STAGGER + SPREAD_SLOT_ENTRANCE_FADE
            self.set_timer(total, self._focus_first_slot)

    def _focus_first_slot(self) -> None:
        """Focus the first unrevealed slot after entrance animation."""
        unrevealed = [s for s in self.query(SpreadSlot) if not s.is_revealed]
        if unrevealed:
            unrevealed[0].focus()

    @staticmethod
    def _animate_slot_entrance(slot: SpreadSlot) -> None:
        slot.styles.animate("opacity", 1.0, duration=SPREAD_SLOT_ENTRANCE_FADE, easing=EASE)
        slot.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, 0)),
            duration=SPREAD_SLOT_ENTRANCE_FADE,
            easing=EASE_SPRING,
        )

    # -- Flip phase --

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
            self._detail.show(
                slots[0] if slots else None,
                sync_interp=self._sync_interp_layout,
                fit_height=lambda: self._dialog.fit_height(self._w_main_area, self._detail.visible),
            )
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
        self._detail.update(event.slot)

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

    # -- Detail toggle --

    def action_toggle_detail(self) -> None:
        if self._phase != Phase.DONE:
            return
        if self._detail.visible:
            if self._box.active_box == "detail":
                self._box.active_box = "spread"
                self._box.update_highlights()
                self._box.focus_widget()
            self._detail.hide(sync_interp=self._sync_interp_layout, center_spread=self._center_spread_area)
        else:
            self._detail.show(
                sync_interp=self._sync_interp_layout,
                fit_height=lambda: self._dialog.fit_height(self._w_main_area, self._detail.visible),
            )
            slots = list(self.query(SpreadSlot))
            if slots:
                self._detail.update(slots[0])
                slots[0].focus()
        self._update_phase_ui()

    # -- Layout helpers --

    def _sync_interp_layout(self) -> None:
        self._dialog.sync_layout(self._detail.visible, self.size.width)

    def _center_spread_area(self) -> None:
        """Reset main area offset to origin (with animation if enabled)."""
        target = ScalarOffset.from_offset(Offset(0, 0))
        if self.app.animation_enabled:
            self._w_main_area.styles.animate("offset", target, duration=0.22, easing=EASE)
        else:
            self._w_main_area.styles.offset = (0, 0)

    # -- Interpretation --

    def action_interpret(self) -> None:
        if self._phase == Phase.DONE and not self._dialog.is_streaming:
            self._cancelled = False
            self._dialog.show(
                sync_layout=self._sync_interp_layout,
                fit_height=lambda: self._dialog.fit_height(self._w_main_area, self._detail.visible),
            )
            self._dialog.run(self._drawn_cards, self._question, lambda: self._cancelled)

    def action_handle_back(self) -> None:
        if self._dialog.is_visible:
            def on_confirm(confirmed: bool) -> None:
                if confirmed:
                    self._cancelled = True
                    self._dialog.stop()
                    go_home(self)
            self.app.push_screen(ConfirmExitInterpretation(), callback=on_confirm)
        else:
            go_home(self)

    def on_resize(self, event: Resize) -> None:
        if self._detail.visible:
            self._detail._fit_height()
        self._dialog.fit_height(self._w_main_area, self._detail.visible)
        self._sync_interp_layout()

    # -- Focus navigation --

    def on_key(self, event: Key) -> None:
        if event.key == "shift+tab":
            event.stop()
            self._box.cycle(-1)

    def key_tab(self, event: Key) -> None:
        event.stop()
        self._box.cycle(1)

    def key_left(self) -> None:
        if self._box.active_box not in ("detail", "interp"):
            self._box.focus_neighbor("left", self._phase, self._n_positions)

    def key_right(self) -> None:
        if self._box.active_box not in ("detail", "interp"):
            self._box.focus_neighbor("right", self._phase, self._n_positions)

    def key_up(self) -> None:
        if self._box.active_box == "interp":
            self._w_interp.scroll_up(animate=True)
        elif self._box.active_box == "detail":
            self.query_one("#card-preview").scroll_up(animate=True)
        else:
            self._box.focus_neighbor("up", self._phase, self._n_positions)

    def key_down(self) -> None:
        if self._box.active_box == "interp":
            self._w_interp.scroll_down(animate=True)
        elif self._box.active_box == "detail":
            self.query_one("#card-preview").scroll_down(animate=True)
        else:
            self._box.focus_neighbor("down", self._phase, self._n_positions)

    def on_descendant_focus(self, event: DescendantFocus) -> None:
        self._box.on_focus_change(event.widget)
