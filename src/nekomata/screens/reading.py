"""Reading screen — displays drawn cards and triggers AI interpretation."""

import asyncio
import logging

from rich.console import Group
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.events import Key
from textual.message import Message
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Static

from nekomata.ai.interpreter import InterpretationError, get_interpreter
from nekomata.card.deck import Deck
from nekomata.card.types import DrawnCard
from nekomata.render.animations import animate_reveal
from nekomata.render.card_renderer import (
    render_card_face,
    render_card_text,
    render_card_detail,
    render_card_image,
    render_card_image_detail,
)
from nekomata.screens.interpretation import InterpretationScreen
from nekomata.screens.widgets import focus_sibling, go_home
from nekomata.spread import get_spread

log = logging.getLogger(__name__)

_WAITING_DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class CardWidget(Static):
    """A focusable widget that renders a single drawn card."""

    can_focus = True

    DEFAULT_CSS = """
    CardWidget {
        margin: 0 1 1 1;
        height: auto;
        width: auto;
        padding: 1 1;
        border: round #313244;
        background: #181825;
        content-align: center middle;
    }
    CardWidget:focus {
        border: round #cba6f7;
        background: #1e1e2e;
    }
    CardWidget:hover {
        background: #1e1e2e;
    }
    CardWidget.selected {
        background: #1e1e2e;
        border: round #cba6f7;
    }
    CardWidget.selected:focus {
        border: round #cba6f7;
    }
    CardWidget.reversed {
        border: round #b4befe;
    }
    CardWidget.reversed.selected {
        border: round #cba6f7;
    }
    CardWidget.reversed:focus {
        border: round #b4befe;
    }
    """

    class Selected(Message):
        """Posted when a card widget is clicked, focused, or Enter-pressed."""

        def __init__(self, drawn_card: DrawnCard, widget: "CardWidget") -> None:
            super().__init__()
            self.drawn_card = drawn_card
            self.widget = widget

    def __init__(self, drawn: DrawnCard, render_mode: str = "compact") -> None:
        self._drawn = drawn
        face = None
        if render_mode != "text":
            face = render_card_face(drawn, size=render_mode)
        if face is None:
            face = render_card_text(drawn, width=28)
        description = Text(
            f"{drawn.position.name}\n{drawn.position.description}",
            style="#a6adc8",
            justify="center",
        )
        super().__init__(Group(face, description))
        if drawn.is_reversed:
            self.add_class("reversed")

    def on_click(self) -> None:
        self.post_message(self.Selected(self._drawn, self))

    def on_focus(self) -> None:
        self.post_message(self.Selected(self._drawn, self))

    def key_enter(self) -> None:
        self.post_message(self.Selected(self._drawn, self))


class ReadingAction(Static):
    """Focusable action row for the reading screen."""

    can_focus = True

    DEFAULT_CSS = """
    ReadingAction {
        width: 24;
        height: 3;
        margin: 0 1;
        padding: 0 2;
        border: round #313244;
        background: #181825;
        color: #a6adc8;
        content-align: center middle;
    }
    ReadingAction:hover {
        background: #1e1e2e;
        color: #cdd6f4;
    }
    ReadingAction:focus {
        background: #1e1e2e;
        border: round #cba6f7;
        color: #cba6f7;
        text-style: bold;
    }
    ReadingAction.primary {
        color: #cba6f7;
    }
    """

    class Selected(Message):
        """Posted when an action is activated."""

        def __init__(self, action_id: str) -> None:
            super().__init__()
            self.action_id = action_id

    def on_click(self) -> None:
        if self.id:
            self.post_message(self.Selected(self.id))

    def key_enter(self) -> None:
        if self.id:
            self.post_message(self.Selected(self.id))


class ReadingScreen(Screen):
    """Displays drawn cards in the chosen spread layout and triggers AI interpretation."""

    BINDINGS = [
        ("i", "interpret", "Interpret"),
        ("q", "handle_escape", "Back"),
        ("escape", "handle_escape", "Back"),
    ]

    DEFAULT_CSS = """
    ReadingScreen {
        align: center top;
    }
    ReadingScreen #question-display {
        text-align: center;
        color: #a6adc8;
        margin: 0 0 0 0;
    }
    ReadingScreen #spread-label {
        text-align: center;
        color: #6c7086;
        margin: 0 0 1 0;
    }
    ReadingScreen #main-area {
        height: 1fr;
        margin-top: 1;
    }
    ReadingScreen #cards-container {
        width: 1fr;
        height: 1fr;
        layout: grid;
        grid-gutter: 1 2;
        border: round #313244;
        background: #11111b;
        padding: 1 1;
        align: center middle;
    }
    ReadingScreen #cards-container.spread-1 {
        grid-size: 1;
        grid-columns: 1fr;
        grid-rows: 1fr;
        align: center middle;
    }
    ReadingScreen #cards-container.spread-3 {
        grid-size: 3 1;
        grid-columns: 1fr 1fr 1fr;
        grid-rows: 1fr;
    }
    ReadingScreen #cards-container.spread-5 {
        grid-size: 3 2;
        grid-columns: 1fr 1fr 1fr;
        grid-rows: 1fr 1fr;
    }
    ReadingScreen #cards-container.spread-10 {
        grid-size: 5 2;
        grid-columns: 1fr 1fr 1fr 1fr 1fr;
        grid-rows: 1fr 1fr;
    }
    ReadingScreen #card-preview {
        width: 1fr;
        height: 1fr;
        border: round #45475a;
        background: #181825;
        padding: 1 2;
        margin-left: 1;
    }
    ReadingScreen #actions {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    ReadingScreen #waiting-msg {
        color: #cba6f7;
        text-align: center;
    }
    ReadingScreen #hints {
        width: 100%;
        height: auto;
        color: #6c7086;
        text-align: center;
        margin-top: 1;
    }
    ReadingScreen #error-msg {
        color: #f38ba8;
        text-align: center;
    }
    """

    def __init__(self, spread_key: str, question: str) -> None:
        super().__init__()
        self._spread_key = spread_key
        self._question = question
        self._drawn_cards: list[DrawnCard] = []
        self._dot_timer: Timer | None = None
        self._dot_idx = 0
        self._last_preview_id: str | None = None
        self._cancelled = False

    def compose(self) -> ComposeResult:
        yield Static(self._question, id="question-display")
        yield Static("", id="spread-label")
        with Horizontal(id="main-area"):
            with Vertical(id="cards-container"):
                pass
            with Vertical(id="card-preview"):
                yield Static("Select a card", id="preview-placeholder")
        with Center(id="actions"):
            action = ReadingAction("Interpret", id="interpret")
            action.add_class("primary")
            yield action
            yield ReadingAction("Home", id="home")
        yield Static("↑/↓ move · Enter confirm · I interpret · Q back", id="hints")

    def on_mount(self) -> None:
        """Draw cards from the deck and mount animated CardWidgets."""
        self._draw_and_mount(animation_enabled=self.app.animation_enabled)

    def on_unmount(self) -> None:
        """Stop waiting animation timers when screen is removed."""
        if self._dot_timer is not None:
            self._dot_timer.stop()
            self._dot_timer = None

    def _draw_and_mount(self, animation_enabled: bool = True) -> None:
        """Shuffle, draw cards, and mount CardWidgets."""
        spread = get_spread(self._spread_key)
        deck = Deck()
        deck.shuffle()
        app = self.app
        spread.draw(deck, reversal_prob=app.reversal_prob)
        self._drawn_cards = spread.drawn_cards
        self._last_preview_id = None

        app.spread_name = spread.name
        label = f"{spread.name}"
        if spread.description:
            label += f"  ·  {spread.description}"
        n_up = sum(1 for dc in self._drawn_cards if not dc.is_reversed)
        n_rev = len(self._drawn_cards) - n_up
        if n_rev > 0:
            label += f"  ·  {n_up} upright / {n_rev} reversed"
        self.query_one("#spread-label", Static).update(label)

        # Reset preview panel
        preview = self.query_one("#card-preview")
        preview.remove_children()
        preview.mount(Static("Select a card"))

        # Clear and repopulate the spread layout canvas.
        container = self.query_one("#cards-container")
        container.remove_children()
        for count in (1, 3, 5, 10):
            container.remove_class(f"spread-{count}")
        container.add_class(f"spread-{len(self._drawn_cards)}")
        mode = app.render_mode

        widgets: list[CardWidget] = []
        for i, dc in enumerate(self._drawn_cards):
            widget = CardWidget(dc, render_mode=mode)
            widgets.append(widget)
            if animation_enabled:
                self.set_timer(
                    max(i * 0.15, 0.01),
                    lambda w=widget: self._reveal_card(w),
                )
        container.mount(*self._ordered_spread_widgets(widgets))

        if animation_enabled:
            self.set_timer(len(self._drawn_cards) * 0.15 + 0.5, self._focus_first_card)
        else:
            self._focus_first_card()

    @staticmethod
    def _ordered_spread_widgets(widgets: list[CardWidget]) -> list[CardWidget]:
        """Return cards in a visual order that resembles the selected spread."""
        count = len(widgets)
        if count == 5:
            return [widgets[4], widgets[0], widgets[1], widgets[3], widgets[2]]
        if count == 10:
            return [
                widgets[4], widgets[0], widgets[1], widgets[5], widgets[9],
                widgets[3], widgets[2], widgets[6], widgets[7], widgets[8],
            ]
        return widgets

    def _focus_first_card(self) -> None:
        cards = list(self.query(CardWidget))
        if cards:
            cards[0].focus()

    @staticmethod
    def _reveal_card(widget: CardWidget) -> None:
        widget.run_worker(animate_reveal(widget))

    def _show_waiting(self) -> None:
        """Replace action buttons with spinner."""
        self.query_one("#interpret").display = False
        self.query_one("#home").display = False
        actions = self.query_one("#actions")
        self._dot_idx = 0
        actions.mount(Static(f"{_WAITING_DOTS[0]}  Interpreting...", id="waiting-msg"))
        self._dot_timer = self.set_interval(0.08, self._tick_dots)
        self.query_one("#hints", Static).update("Interpreting... · Esc cancel")

    def _tick_dots(self) -> None:
        """Cycle the spinner dot."""
        self._dot_idx = (self._dot_idx + 1) % len(_WAITING_DOTS)
        try:
            self.query_one("#waiting-msg", Static).update(
                f"{_WAITING_DOTS[self._dot_idx]}  Interpreting..."
            )
        except NoMatches:
            pass

    def _hide_waiting(self) -> None:
        """Stop waiting animation and restore action buttons."""
        if self._dot_timer is not None:
            self._dot_timer.stop()
            self._dot_timer = None
        try:
            self.query_one("#waiting-msg", Static).remove()
        except NoMatches:
            pass
        self.query_one("#interpret").display = True
        self.query_one("#home").display = True
        self.query_one("#hints", Static).update(
            "↑/↓ move · Enter confirm · I interpret · Q back"
        )

    def _show_error(self, message: str) -> None:
        """Show an error message below the action buttons."""
        self._hide_waiting()
        try:
            self.query_one("#error-msg", Static).remove()
        except NoMatches:
            pass
        actions = self.query_one("#actions")
        actions.mount(Static(message, id="error-msg"))

    def on_card_widget_selected(self, event: CardWidget.Selected) -> None:
        """Update the detail preview and mark the selected card."""
        dc = event.drawn_card
        preview_id = f"{dc.card.id}:{dc.is_reversed}"
        if self._last_preview_id == preview_id:
            return
        self._last_preview_id = preview_id
        for w in self.query(CardWidget):
            w.remove_class("selected")
        event.widget.add_class("selected")
        preview = self.query_one("#card-preview")
        preview.remove_children()
        if self.app.render_mode != "text":
            img_detail = render_card_image_detail(dc)
            if img_detail:
                preview.mount(Static(img_detail))
                return
        preview.mount(Static(render_card_detail(dc)))

    def on_reading_action_selected(self, event: ReadingAction.Selected) -> None:
        """Handle reading action activation."""
        if event.action_id == "home":
            go_home(self)
        elif event.action_id == "interpret":
            self._do_interpret()

    @property
    def _is_waiting(self) -> bool:
        """Whether AI interpretation is in progress."""
        return self._dot_timer is not None

    def action_interpret(self) -> None:
        """I key binding — trigger AI interpretation."""
        if not self._is_waiting:
            self._do_interpret()

    def action_handle_escape(self) -> None:
        """Cancel interpretation if waiting, otherwise go home."""
        if self._is_waiting:
            self._cancelled = True
            self._hide_waiting()
        else:
            go_home(self)

    def _do_interpret(self) -> None:
        """Trigger AI interpretation in a background worker."""
        self._cancelled = False
        self._show_waiting()
        self.run_worker(self._run_interpretation(), exclusive=True)

    def key_down(self) -> None:
        """Move focus down through cards, then action buttons."""
        if isinstance(self.focused, CardWidget):
            if not self._focus_card(1):
                self._focus_first_button()
        elif isinstance(self.focused, ReadingAction):
            self._focus_button(1)

    def key_up(self) -> None:
        """Move focus up through action buttons, then cards."""
        if isinstance(self.focused, CardWidget):
            self._focus_card(-1)
        elif isinstance(self.focused, ReadingAction):
            if not self._focus_button(-1):
                self._focus_last_card()

    def key_tab(self, event: Key) -> None:
        """Cycle focus: if on a card, go to first button; if on button, go to first card."""
        event.stop()
        if isinstance(self.focused, CardWidget):
            buttons = list(self.query(ReadingAction))
            if buttons:
                buttons[0].focus()
        elif isinstance(self.focused, ReadingAction):
            cards = list(self.query(CardWidget))
            if cards:
                cards[0].focus()

    def _focus_card(self, delta: int) -> bool:
        """Focus a neighboring card; return whether focus moved."""
        cards = list(self.query(CardWidget))
        if not cards:
            return False
        try:
            idx = cards.index(self.focused)
        except ValueError:
            cards[0].focus()
            return True
        new_idx = idx + delta
        if 0 <= new_idx < len(cards):
            cards[new_idx].focus()
            return True
        return False

    def _focus_button(self, delta: int) -> bool:
        """Focus a neighboring action button; return whether focus moved."""
        buttons = [button for button in self.query(ReadingAction) if button.display]
        if not buttons:
            return False
        try:
            idx = buttons.index(self.focused)
        except ValueError:
            buttons[0].focus()
            return True
        new_idx = idx + delta
        if 0 <= new_idx < len(buttons):
            buttons[new_idx].focus()
            return True
        return False

    def _focus_first_button(self) -> None:
        """Focus the first visible action button."""
        buttons = [button for button in self.query(ReadingAction) if button.display]
        if buttons:
            buttons[0].focus()

    def _focus_last_card(self) -> None:
        """Focus the last card in the card list."""
        cards = list(self.query(CardWidget))
        if cards:
            cards[-1].focus()

    async def _run_interpretation(self) -> None:
        """Run interpretation via the configured AI backend."""
        try:
            config = self.app.config
            interp = get_interpreter(config)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, interp.interpret, self._drawn_cards, self._question
            )
        except InterpretationError as exc:
            if not self.is_mounted or self._cancelled:
                return
            self._show_error(f"Interpretation failed: {exc}")
            return
        except Exception as exc:
            if not self.is_mounted or self._cancelled:
                return
            msg = str(exc)
            if "api_key" in msg.lower() or "api key" in msg.lower() or "unauthorized" in msg.lower():
                self._show_error(
                    "API key not configured. "
                    "Set ai.api_key in config.toml to enable interpretation."
                )
            else:
                self._show_error(f"Interpretation failed: {exc}")
            return
        # Guard: screen may have been popped or interpretation cancelled
        if not self.is_mounted or self._cancelled:
            return
        self._hide_waiting()
        self.app.push_screen(InterpretationScreen(
            result, self._drawn_cards, self._question,
            spread_name=self.app.spread_name,
        ))
