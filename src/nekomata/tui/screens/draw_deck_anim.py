"""Deck entrance/exit animations for DrawScreen."""

from __future__ import annotations

import asyncio

from nekomata.core.render.styles import EASE
from nekomata.tui.render.animations import staggered_entrance
from nekomata.tui.screens.draw_constants import (
    DECK_ENTRANCE_FADE,
    DECK_ENTRANCE_STAGGER,
    DECK_EXIT_DURATION,
)
from nekomata.tui.screens.draw_phase import Phase
from nekomata.tui.screens.draw_widgets import DeckCard


class DeckAnimMixin:
    """Deck animation methods extracted from DrawScreen."""

    # -- Exit --

    async def _animate_deck_exit(self) -> None:
        """Fade out the deck section, then hide it to free layout space for the spread."""
        if not self.app.animation_enabled:
            self._w_deck_section.display = False
            return
        self._w_deck_section.styles.animate("opacity", 0.0, duration=DECK_EXIT_DURATION, easing=EASE)
        await asyncio.sleep(DECK_EXIT_DURATION + 0.02)
        self._w_deck_section.display = False
        self._w_deck_section.styles.opacity = 1.0  # reset for next DrawScreen

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
