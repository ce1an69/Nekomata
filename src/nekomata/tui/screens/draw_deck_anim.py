"""Deck entrance/exit animations for DrawScreen."""

from __future__ import annotations

from nekomata.core.render.styles import EASE
from nekomata.tui.render.animations import staggered_entrance
from nekomata.tui.screens.draw_constants import (
    DECK_ENTRANCE_FADE,
    DECK_ENTRANCE_STAGGER,
)
from nekomata.tui.screens.draw_phase import Phase
from nekomata.tui.screens.draw_widgets import DeckCard


class DeckAnimMixin:
    """Deck animation methods extracted from DrawScreen."""

    # -- Exit --

    def _hide_deck_section(self) -> None:
        """Hide the deck section immediately to free layout space for the spread."""
        self._w_deck_section.display = False

    # -- Entrance --

    def _animate_deck_entrance(self) -> None:
        self._dealing = True
        cards = list(self.query(DeckCard))
        staggered_entrance(
            self,
            cards,
            stagger=DECK_ENTRANCE_STAGGER,
            duration=DECK_ENTRANCE_FADE,
            dy=1,
            easing=EASE,
            on_complete=self._enable_deck_selection,
        )

    def _enable_deck_selection(self) -> None:
        self._dealing = False
        if self.phase != Phase.PICK:
            return
        deck_cards = list(self.query(DeckCard))
        if deck_cards:
            deck_cards[0].focus()
