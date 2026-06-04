"""Deck entrance/exit animations for DrawScreen."""

from __future__ import annotations

from textual.css.scalar import ScalarOffset
from textual.geometry import Offset

from nekomata.core.render.styles import EASE
from nekomata.tui.screens.draw_constants import (
    DECK_ENTRANCE_FADE,
    DECK_ENTRANCE_STAGGER,
    DECK_HIDE_DELAY,
)
from nekomata.tui.screens.draw_phase import Phase
from nekomata.tui.screens.draw_widgets import DeckCard


class DeckAnimMixin:
    """Deck animation methods extracted from DrawScreen."""

    # -- Exit --

    def _animate_deck_exit(self) -> None:
        """Fade out the deck section, then hide it from layout."""
        if self.app.animation_enabled:
            self._w_deck_section.styles.animate("opacity", 0.0, duration=DECK_HIDE_DELAY, easing=EASE)
            self.set_timer(DECK_HIDE_DELAY, self._hide_deck)
        else:
            self._w_deck_section.display = False

    def _hide_deck(self) -> None:
        self._w_deck_section.display = False

    # -- Entrance --

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
        card.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, 0)),
            duration=DECK_ENTRANCE_FADE,
            easing=EASE,
        )

    def _enable_deck_selection(self) -> None:
        self._dealing = False
        if self._phase != Phase.PICK:
            return
        deck_cards = list(self.query(DeckCard))
        if deck_cards:
            deck_cards[0].focus()
