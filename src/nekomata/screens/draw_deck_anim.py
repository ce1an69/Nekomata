"""Deck entrance/exit/spread-recenter animations for DrawScreen."""

from __future__ import annotations

from textual.css.scalar import ScalarOffset
from textual.geometry import Offset

from nekomata.render.styles import EASE
from nekomata.screens.draw_widgets import (
    DECK_ENTRANCE_FADE,
    DECK_ENTRANCE_STAGGER,
    DECK_HIDE_DELAY,
    DeckCard,
)


class DeckAnimMixin:
    """Deck animation methods extracted from DrawScreen."""

    def _hide_deck(self) -> None:
        self._w_deck_section.display = False
        self._animate_spread_recenter()

    def _animate_spread_recenter(self) -> None:
        from nekomata.screens.draw_widgets import SPREAD_RECENTER_DURATION, SPREAD_RECENTER_OFFSET

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
        if self.app.animation_enabled:
            self._w_deck_section.styles.animate(
                "opacity", 0.0, duration=0.22, easing=EASE
            )
            self._w_deck_section.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, -2)),
                duration=0.28,
                easing=EASE,
            )
        for i, card in enumerate(
            c for c in self.query(DeckCard) if not c.has_class("picked")
        ):
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
        card.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, 0)),
            duration=DECK_ENTRANCE_FADE,
            easing=EASE,
        )

    def _enable_deck_selection(self) -> None:
        from nekomata.screens.draw import Phase

        self._dealing = False
        if self._phase != Phase.PICK:
            return
        deck_cards = list(self.query(DeckCard))
        if deck_cards:
            deck_cards[0].focus()
