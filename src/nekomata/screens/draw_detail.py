"""Detail panel manager for the draw screen."""

from textual.css.scalar import ScalarOffset
from textual.geometry import Offset
from textual.widgets import Static

from nekomata.render.card_renderer import render_card_detail, render_card_full_detail_widgets
from nekomata.render.styles import EASE


class DetailPanel:
    """Manages the card detail side panel: show/hide, content updates."""

    def __init__(self, screen) -> None:
        self._screen = screen
        self._visible = False
        self._last_preview_id: str | None = None
        self._pending_center_spread = None
        # Widget reference (set after mount)
        self._w_preview = None

    def cache_widgets(self) -> None:
        self._w_preview = self._screen.query_one("#card-preview")

    @property
    def visible(self) -> bool:
        return self._visible

    # -- Show / Hide --

    def show(self, slot=None, sync_interp=None, fit_height=None) -> None:
        """Display the detail panel with entrance animation."""
        self._visible = True
        if sync_interp:
            sync_interp()
        self._w_preview.display = True
        self._fit_height()
        if fit_height:
            fit_height()
        self._screen.call_after_refresh(self._fit_height)
        if self._screen.app.animation_enabled:
            self._w_preview.styles.opacity = 0
            self._w_preview.styles.offset = (4, 0)
        self._w_preview.add_class("visible")
        if self._screen.app.animation_enabled:
            self._w_preview.styles.animate("opacity", 1.0, duration=0.24, easing=EASE)
            self._w_preview.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 0)),
                duration=0.32,
                easing=EASE,
            )
        self._last_preview_id = None
        if slot is not None:
            self.update(slot)

    def hide(self, sync_interp=None, center_spread=None) -> None:
        """Hide the detail panel with exit animation."""
        self._visible = False
        self._pending_center_spread = center_spread
        if sync_interp:
            sync_interp()
        if self._screen.app.animation_enabled:
            self._w_preview.styles.animate("opacity", 0.0, duration=0.18, easing=EASE)
            self._w_preview.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(4, 0)),
                duration=0.24,
                easing=EASE,
            )
            self._screen.set_timer(0.24, self._finish_hide)
        else:
            self._finish_hide()

    def _fit_height(self) -> None:
        """Match detail panel height to the main area bottom edge.

        This ensures the detail panel doesn't extend past the spread area
        or interp dialog, whichever is lower on screen.
        """
        main_area = self._screen.query_one("#main-area")
        interp = self._screen.query_one("#interp-dialog")
        bottom = main_area.region.y + main_area.region.height
        if interp.has_class("visible"):
            bottom = max(bottom, interp.region.y + interp.region.height)
        self._w_preview.styles.height = max(1, bottom - 1)

    def _finish_hide(self) -> None:
        """Complete the hide animation: remove panel from layout, then recenter spread."""
        self._w_preview.remove_class("visible")
        self._w_preview.display = False
        self._w_preview.styles.height = "1fr"
        if self._pending_center_spread:
            self._pending_center_spread()
            self._pending_center_spread = None

    # -- Content --

    def update(self, slot) -> None:
        """Update the detail panel content for the given spread slot."""
        if not self._visible or not slot.drawn_card:
            return
        dc = slot.drawn_card
        preview_id = f"{dc.card.id}:{dc.is_reversed}"
        if self._last_preview_id == preview_id:
            return
        self._last_preview_id = preview_id

        self._w_preview.remove_children()

        if self._screen.app.render_mode != "text":
            result = render_card_full_detail_widgets(dc)
            if result is not None:
                from textual.containers import Horizontal
                img_widget, text_panel = result
                self._w_preview.mount(Horizontal(img_widget, classes="card-origin-frame"))
                self._w_preview.mount(Static(text_panel))
                return

        self._w_preview.mount(Static(render_card_detail(dc)))
