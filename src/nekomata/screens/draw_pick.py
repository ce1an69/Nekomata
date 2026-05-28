"""PICK phase logic — card picking from deck for DrawScreen."""

from __future__ import annotations

import asyncio
import logging

from textual.css.scalar import ScalarOffset
from textual.geometry import Offset

from nekomata.render.card_renderer import preload_all_async, preload_card_image_async
from nekomata.render.styles import EASE, EASE_SPRING
from nekomata.screens.draw_widgets import (
    PICK_COMPLETE_DELAY,
    SPREAD_SLOT_ENTRANCE_FADE,
    SPREAD_SLOT_ENTRANCE_STAGGER,
    DeckCard,
    SpreadSlot,
)

log = logging.getLogger(__name__)


class PickMixin:
    """PICK phase methods extracted from DrawScreen."""

    async def on_deck_card_picked(self, event: DeckCard.Picked) -> None:
        from nekomata.screens.draw import Phase

        if self._phase != Phase.PICK:
            return
        event.stop()

        card_widget = event.card
        if card_widget.has_class("picked"):
            return
        if self._pick_index >= len(self._planned_cards):
            return
        if self._dealing:
            log.debug("Accepting pick while deck entrance animation is still active")
            self._dealing = False
        dc = self._planned_cards[self._pick_index]
        self._drawn_cards.append(dc)

        card_widget.add_class("picked")
        self.run_worker(
            preload_card_image_async(dc.card, dc.is_reversed), exclusive=False
        )

        self._pick_index += 1
        self._update_phase_ui()
        log.debug(
            "Picked card %s/%s in %s phase",
            self._pick_index,
            self._n_positions,
            self._phase.name,
        )

        if self._pick_index >= self._n_positions:
            await self._transition_to_flip()

    async def _transition_to_flip(self) -> None:
        log.debug(
            "Transitioning to flip phase with %s drawn card(s)", len(self._drawn_cards)
        )
        if PICK_COMPLETE_DELAY:
            await asyncio.sleep(PICK_COMPLETE_DELAY)
        await self._reveal_spread()

    async def _reveal_spread(self) -> None:
        from nekomata.screens.draw import Phase

        log.debug("Revealing spread and entering flip phase")
        await preload_all_async([(dc.card, dc.is_reversed) for dc in self._drawn_cards])
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
            total = (
                0.05
                + len(slots) * SPREAD_SLOT_ENTRANCE_STAGGER
                + SPREAD_SLOT_ENTRANCE_FADE
            )
            self.set_timer(total, self._focus_first_slot)

    def _focus_first_slot(self) -> None:
        unrevealed = [s for s in self.query(SpreadSlot) if not s.is_revealed]
        if unrevealed:
            unrevealed[0].focus()

    @staticmethod
    def _animate_slot_entrance(slot: SpreadSlot) -> None:
        slot.styles.animate(
            "opacity", 1.0, duration=SPREAD_SLOT_ENTRANCE_FADE, easing=EASE
        )
        slot.styles.animate(
            "offset",
            ScalarOffset.from_offset(Offset(0, 0)),
            duration=SPREAD_SLOT_ENTRANCE_FADE,
            easing=EASE_SPRING,
        )
