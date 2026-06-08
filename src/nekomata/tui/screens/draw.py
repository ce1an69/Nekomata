"""Draw screen — pick cards from a face-down deck, then flip to reveal."""

import logging
from typing import TYPE_CHECKING, cast

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.css.scalar import ScalarOffset
from textual.events import DescendantFocus, Key, Resize
from textual.geometry import Offset
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Input, Static

from nekomata.core.card.deck import Deck
from nekomata.core.card.types import DrawnCard

if TYPE_CHECKING:
    from nekomata.tui.app import NekomataApp

from nekomata.core.i18n import ORNAMENT
from nekomata.core.render.card_renderer import clear_cache
from nekomata.core.render.styles import C_MAUVE, C_SUBTEXT0, EASE
from nekomata.core.spread import get_spread
from nekomata.tui.screens.box_manager import BoxManager
from nekomata.tui.screens.draw_constants import (
    _STR,
    NUM_DECK_CARDS,
    SPREAD_CENTER_DURATION,
    SPREAD_SLOT_HEIGHT,
    SPREAD_SLOT_WIDTH,
)
from nekomata.tui.screens.draw_css import DRAW_SCREEN_CSS
from nekomata.tui.screens.draw_deck_anim import DeckAnimMixin
from nekomata.tui.screens.draw_detail import DetailPanel
from nekomata.tui.screens.draw_dialog import InterpretationDialog
from nekomata.tui.screens.draw_interpret import InterpretMixin
from nekomata.tui.screens.draw_messages import DetailHideRequested, DetailShowRequested, PhaseChanged
from nekomata.tui.screens.draw_phase import Phase
from nekomata.tui.screens.draw_pick import PickMixin
from nekomata.tui.screens.draw_widgets import DeckCard, SpreadSlot
from nekomata.tui.screens.layout_hints import LayoutHints
from nekomata.tui.screens.stream_handler import StreamHandler

log = logging.getLogger(__name__)


class DrawScreen(DeckAnimMixin, PickMixin, InterpretMixin, Screen):
    """Card drawing screen: pick from deck -> flip to reveal -> detail + interpret."""

    # Reactive phase — watcher posts PhaseChanged Message on transitions.
    phase: reactive[Phase] = reactive(Phase.PICK, repaint=False)

    BINDINGS = [
        Binding("escape", "handle_back", "Back"),
        Binding("i", "interpret", "Interpret", show=False),
        Binding("d", "toggle_detail", "Detail", show=False),
    ]

    DEFAULT_CSS = DRAW_SCREEN_CSS

    def __init__(self, spread_key: str, question: str, *, lang: str = "en") -> None:
        super().__init__()
        self._spread_key = spread_key
        self._question = question
        self._spread = get_spread(spread_key, lang=lang)
        self._deck = Deck()
        self._deck.shuffle()
        self._planned_cards: list[DrawnCard] = []
        self._drawn_cards: list[DrawnCard] = []
        self._pick_index = 0
        self._cancelled = False
        self._dealing = False
        self._pending_flips: int = 0
        self._skip_phase_ui_message = False
        self._n_positions = len(self._spread.positions)
        self._display_order = self._spread.display_order
        self._ordered_positions = [self._spread.positions[i] for i in self._display_order]

        # Follow-up state
        self._followup_remaining: int = self._n_positions
        self._followup_visible: bool = False
        self._followup_active: bool = False
        self._followup_question: str = ""
        self._first_interp_done: bool = False
        self._prev_interp_content: str = ""
        self._initial_interp_content: str = ""
        self._messages_history: list[dict] = []

        self._box = BoxManager(self, self._available_boxes)
        self._current_layout_mode: str = "default"  # "default" | "compact" | "tiny"
        self._detail_stacked: bool = False
        self._current_slot_w: int = 0
        self._current_slot_h: int = 0
        self._stream = StreamHandler(
            screen=self,
            render_content=self._on_stream_render,
            render_hints=self._on_stream_hints,
            scroll_to_bottom=self._on_stream_scroll,
        )
        self._detail = DetailPanel(self)
        self._dialog = InterpretationDialog(
            self, self._box, self._stream, lambda: self._detail.visible
        )

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
            hints = LayoutHints(self.size.width or 120, self.size.height or 40, "compact")
            row_count = hints.deck_row_count
            base_cards_per_row, extra_cards = divmod(NUM_DECK_CARDS, row_count)
            card_index = 0
            with Vertical(id="deck-row"):
                for row_index in range(row_count):
                    row_size = base_cards_per_row + int(row_index < extra_cards)
                    with Horizontal(classes="deck-row-line"):
                        for i in range(card_index, card_index + row_size):
                            yield DeckCard(i)
                    card_index += row_size

        with Horizontal(id="reading-area"):
            with Vertical(id="left-pane"):
                with Horizontal(id="main-area"), Vertical(id="spread-area"):
                    yield Static("", id="spread-label")
                    with Horizontal(id="spread-grid"):
                        for i, pos in enumerate(self._ordered_positions):
                            yield SpreadSlot(i, pos.name)

                with VerticalScroll(id="interp-dialog"):
                    yield Static(_STR["interp_title"], id="interp-dialog-title")
                    yield Static("", id="interp-dialog-content")
                    yield Static("", id="interp-dialog-hints")

            with VerticalScroll(id="card-preview"):
                pass

        yield Static("", id="draw-footer")

        with Vertical(id="followup-section"):
            yield Input(placeholder=_STR["followup_placeholder"], id="followup-input")

    # -- Mount / Unmount --

    def on_mount(self) -> None:
        self._prepare_drawn_cards()

        self._w_deck_section = self.query_one("#deck-section")
        self._w_deck_label = self.query_one("#deck-label", Static)
        self._w_main_area = self.query_one("#main-area")
        self._w_spread_label = self.query_one("#spread-label", Static)
        self._w_spread_grid = self.query_one("#spread-grid")
        self._w_interp = self.query_one("#interp-dialog")
        self._w_interp_content = self.query_one("#interp-dialog-content", Static)
        self._w_interp_hints = self.query_one("#interp-dialog-hints", Static)
        self._w_followup_section = self.query_one("#followup-section")
        self._w_followup_input = self.query_one("#followup-input", Input)
        self._w_footer = self.query_one("#draw-footer", Static)

        self._dialog.cache_widgets()
        self._detail.cache_widgets()

        grid = self._w_spread_grid
        for cls in ("layout-1", "layout-3", "layout-5", "layout-10"):
            grid.remove_class(cls)
        grid.add_class(f"layout-{self._n_positions}")

        self._w_main_area.display = False
        self._apply_responsive_layout()
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
            card, is_reversed = self._deck.draw(cast("NekomataApp", self.app).reversal_prob)
            self._planned_cards.append(DrawnCard(card=card, position=position, is_reversed=is_reversed))

    def on_unmount(self) -> None:
        self._cancelled = True
        self._stream.stop()
        clear_cache()

    # -- Reactive watchers --

    def watch_phase(self, old_phase: Phase, new_phase: Phase) -> None:
        """Post PhaseChanged Message on phase transitions."""
        self.post_message(PhaseChanged(old_phase, new_phase))

    # -- Detail Message handlers --

    @on(DetailShowRequested)
    def _on_detail_show_requested(self, message: DetailShowRequested) -> None:
        self._detail.show(slot=message.slot, sync_interp=self._sync_interp_layout)

    @on(DetailHideRequested)
    def _on_detail_hide_requested(self, message: DetailHideRequested) -> None:
        self._detail.hide(sync_interp=self._sync_interp_layout, center_spread=message.center_spread)

    # -- Layout helpers --

    def _apply_responsive_layout(self) -> None:
        """Toggle responsive CSS classes and runtime styles based on terminal size."""
        hints = LayoutHints(self.size.width, self.size.height, self.app.render_mode)

        new_mode = "tiny" if hints.is_tiny else ("compact" if hints.is_narrow else "default")
        new_stacked = hints.detail_stacked

        if new_mode == "default":
            new_slot_w, new_slot_h = SPREAD_SLOT_WIDTH, SPREAD_SLOT_HEIGHT
        else:
            new_slot_w, new_slot_h = hints.spread_slot_width, hints.spread_slot_height

        if (new_mode == self._current_layout_mode
                and new_stacked == self._detail_stacked
                and new_slot_w == self._current_slot_w
                and new_slot_h == self._current_slot_h):
            return

        # -- Spread grid class --
        grid = self._w_spread_grid
        for cls in ("compact", "tiny"):
            grid.remove_class(cls)
        if new_mode != "default":
            grid.add_class(new_mode)

        # -- Slot runtime sizes --
        if new_mode == "default":
            slot_w, slot_h = SPREAD_SLOT_WIDTH, SPREAD_SLOT_HEIGHT
        else:
            slot_w, slot_h = hints.spread_slot_width, hints.spread_slot_height
        for slot in self.query(SpreadSlot):
            slot.styles.width = slot_w
            slot.styles.height = slot_h
            slot.styles.min_width = slot_w
            slot.styles.min_height = slot_h

        # -- Deck section min-height --
        self._w_deck_section.styles.min_height = hints.deck_section_min_height

        # -- Detail panel stacked mode --
        if new_stacked != self._detail_stacked:
            reading_area = self.query_one("#reading-area")
            preview = self.query_one("#card-preview")
            if new_stacked:
                reading_area.add_class("stacked")
                preview.add_class("stacked")
            else:
                reading_area.remove_class("stacked")
                preview.remove_class("stacked")

        self._current_layout_mode = new_mode
        self._detail_stacked = new_stacked
        self._current_slot_w = new_slot_w
        self._current_slot_h = new_slot_h

    def _sync_interp_layout(self) -> None:
        self._dialog.sync_layout(self._detail.visible, self.size.width)

    def _center_spread_area(self) -> None:
        target = ScalarOffset.from_offset(Offset(0, 0))
        if cast("NekomataApp", self.app).animation_enabled:
            self._w_main_area.styles.animate(
                "offset",
                target,  # type: ignore[arg-type]
                duration=SPREAD_CENTER_DURATION,
                easing=EASE,
            )
        else:
            self._w_main_area.styles.offset = (0, 0)

    # -- Resize --

    def on_resize(self, event: Resize) -> None:
        self._apply_responsive_layout()
        if self._detail.visible:
            self._detail._fit_height()
        self._sync_interp_layout()

    # -- Focus navigation --

    def on_key(self, event: Key) -> None:
        if event.key == "shift+tab":
            event.stop()
            self._box.cycle(-1)
            self._on_box_changed()

    def key_tab(self, event: Key) -> None:
        event.stop()
        self._box.cycle(1)
        self._on_box_changed()

    def key_left(self) -> None:
        if self._box.active_box not in ("detail", "interp"):
            self._box.focus_neighbor("left", self.phase)

    def key_right(self) -> None:
        if self._box.active_box not in ("detail", "interp"):
            self._box.focus_neighbor("right", self.phase)

    def key_up(self) -> None:
        if self._box.active_box == "interp":
            self._w_interp.scroll_up(animate=True)
        elif self._box.active_box == "detail":
            self.query_one("#card-preview").scroll_up(animate=True)
        else:
            self._box.focus_neighbor("up", self.phase)

    def key_down(self) -> None:
        if self._box.active_box == "interp":
            self._w_interp.scroll_down(animate=True)
        elif self._box.active_box == "detail":
            self.query_one("#card-preview").scroll_down(animate=True)
        else:
            self._box.focus_neighbor("down", self.phase)

    def on_descendant_focus(self, event: DescendantFocus) -> None:
        self._box.on_focus_change(event.widget)
