"""Interpretation dialog manager for the draw screen."""

from rich.text import Text

from textual.css.scalar import ScalarOffset
from textual.geometry import Offset

from nekomata.render.styles import C_RED, EASE
from nekomata.screens.stream_handler import StreamHandler

# Layout constants
INTERP_PANEL_HEIGHT = "46%"  # CSS-only; runtime code uses _panel_height_cells()
INTERP_PANEL_HEIGHT_RATIO = 0.46
INTERP_MIN_HEIGHT = 14
INTERP_MAX_HEIGHT = 30
INTERP_SIDE_MARGIN = 1
INTERP_DETAIL_GAP = 0
INTERP_FULL_SIDE_MARGIN = 5
INTERP_FULL_WIDTH_CORRECTION = 4
INTERP_FULLSCREEN_VERTICAL_CHROME = 5
INTERP_FULLSCREEN_SIDE_MARGIN = 1
DETAIL_PANEL_WIDTH = 66


class InterpretationDialog:
    """Manages the interpretation dialog: show/hide, layout, streaming."""

    def __init__(self, screen, box_manager, stream: StreamHandler) -> None:
        self._screen = screen
        self._box = box_manager
        self._stream = stream
        self._streaming = False
        self._fullscreen = False
        self._prev_detail_visible = False
        self._prev_main_area_display = True
        self._prev_status_display = True
        self._height_timers: list = []
        # Cache widget references (set after mount)
        self._w_interp = None
        self._w_content = None
        self._w_hints = None
        self._w_status = None

    def cache_widgets(self) -> None:
        self._w_interp = self._screen.query_one("#interp-dialog")
        self._w_content = self._screen.query_one("#interp-dialog-content")
        self._w_hints = self._screen.query_one("#interp-dialog-hints")
        self._w_status = self._screen.query_one("#status")

    @property
    def is_visible(self) -> bool:
        return self._w_interp.has_class("visible")

    @property
    def is_streaming(self) -> bool:
        return self._streaming

    # -- Layout --

    @property
    def fullscreen(self) -> bool:
        return self._fullscreen

    def toggle_fullscreen(self, main_area) -> None:
        """Toggle fullscreen mode: hide spread, keep detail available."""
        self._fullscreen = not self._fullscreen
        spread_area = self._screen.query_one("#spread-area")
        detail = self._screen._detail
        if self._fullscreen:
            self._prev_detail_visible = detail.visible
            self._prev_main_area_display = main_area.display
            self._prev_status_display = self._w_status.display
            spread_area.display = False
            main_area.display = False
            self._w_status.display = False
            self._start_height_fullscreen()
        else:
            self._animate_interp_height(
                self._w_interp.region.height,
                self._panel_height_cells(),
                on_complete=lambda: self._restore_from_fullscreen(spread_area, detail, main_area),
            )

    def _start_height_fullscreen(self) -> None:
        self._w_interp.add_class("fullscreen")
        self._cancel_height_anim()
        self.sync_layout(self._screen._detail.visible, self._screen.size.width)
        self._w_interp.styles.height = max(
            INTERP_MIN_HEIGHT,
            self._screen.size.height - INTERP_FULLSCREEN_VERTICAL_CHROME,
        )

    def _restore_from_fullscreen(self, spread_area, detail, main_area) -> None:
        """Restore spread and detail after fullscreen exit animation."""
        self._w_interp.remove_class("fullscreen")
        self._w_interp.styles.height = self._panel_height_cells()
        main_area.display = self._prev_main_area_display
        self._w_status.display = self._prev_status_display
        spread_area.display = True
        if self._prev_detail_visible and not detail.visible:
            detail.show(
                sync_interp=lambda: self.sync_layout(True, self._screen.size.width),
                fit_height=lambda: self.fit_height(main_area, True),
            )
        elif not self._prev_detail_visible and detail.visible:
            detail.hide(sync_interp=lambda: self.sync_layout(False, self._screen.size.width))
        else:
            self.sync_layout(detail.visible, self._screen.size.width)
        self.fit_height(main_area, detail.visible)

    def _cancel_height_anim(self) -> None:
        for t in self._height_timers:
            t.stop()
        self._height_timers.clear()

    def _panel_height_cells(self) -> int:
        return max(
            INTERP_MIN_HEIGHT,
            min(
                INTERP_MAX_HEIGHT,
                round(self._screen.size.height * INTERP_PANEL_HEIGHT_RATIO),
            ),
        )

    def _animate_interp_height(
        self, from_height: int, to_height: int, on_complete=None
    ) -> None:
        """Animate interp dialog height using Textual's native animation."""
        self._cancel_height_anim()
        if not self._screen.app.animation_enabled:
            self._w_interp.styles.height = to_height
            if on_complete:
                on_complete()
            return
        self._w_interp.styles.height = from_height
        duration = 0.28
        self._w_interp.styles.animate(
            "height", to_height, duration=duration, easing="out_cubic"
        )
        if on_complete:
            timer = self._screen.set_timer(duration + 0.01, on_complete)
            self._height_timers.append(timer)

    def sync_layout(self, detail_visible: bool, screen_width: int) -> None:
        """Adjust interp dialog width to share space with the detail panel.

        When detail is visible, the interp panel shrinks to avoid overlap.
        When detail is hidden, it expands to full available width.
        """
        if self._fullscreen:
            self._w_interp.styles.margin = (0, 1, 2, 1)
            if detail_visible:
                self._w_interp.add_class("detail-visible")
                self._w_interp.styles.width = max(
                    40,
                    screen_width - DETAIL_PANEL_WIDTH - INTERP_FULLSCREEN_SIDE_MARGIN * 2,
                )
            else:
                self._w_interp.remove_class("detail-visible")
                self._w_interp.styles.width = max(
                    40,
                    screen_width - INTERP_FULLSCREEN_SIDE_MARGIN * 2,
                )
            return

        if detail_visible:
            self._w_interp.add_class("detail-visible")
            self._w_interp.styles.margin = (0, 1, 2, 1)
            self._w_interp.styles.width = max(
                40,
                screen_width - DETAIL_PANEL_WIDTH
                - INTERP_SIDE_MARGIN - INTERP_DETAIL_GAP,
            )
        else:
            self._w_interp.remove_class("detail-visible")
            self._w_interp.styles.margin = (0, 1, 1, 1)
            self._w_interp.styles.width = max(
                40,
                screen_width - INTERP_FULL_SIDE_MARGIN * 2
                + INTERP_FULL_WIDTH_CORRECTION,
            )

    def fit_height(self, main_area, detail_visible: bool) -> None:
        """Size the interp panel to fill available vertical space."""
        bottom = main_area.region.y + main_area.region.height
        if self.is_visible:
            bottom = max(bottom, self._w_interp.region.y + self._w_interp.region.height)
        if detail_visible:
            preview = self._screen.query_one("#card-preview")
            preview.styles.height = max(1, bottom - 1)

    # -- Show / Hide --

    def show(self, sync_layout=None, fit_height=None) -> None:
        """Display the interpretation dialog with entrance animation."""
        self._streaming = True
        self._box.active_box = "interp"
        self._box.update_highlights()
        if sync_layout:
            sync_layout()
        if fit_height:
            fit_height()
        self._w_interp.display = True
        if self._screen.app.animation_enabled:
            self._w_interp.styles.opacity = 0
            self._w_interp.styles.offset = (0, 2)
        self._w_interp.add_class("visible")
        if self._screen.app.animation_enabled:
            self._w_interp.styles.animate("opacity", 1.0, duration=0.30, easing=EASE)
            self._w_interp.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 0)),
                duration=0.34,
                easing=EASE,
            )
        self._stream.reset()
        self._w_status.update("")

    def hide(self, update_phase_ui, sync_layout=None, fit_height=None) -> None:
        """Hide the dialog with exit animation, then update phase UI."""
        self._streaming = False
        self._stream.stop()
        was_fullscreen = self._fullscreen
        if self._fullscreen:
            self._fullscreen = False
            self._cancel_height_anim()
        self._box.active_box = "spread"
        self._box.update_highlights()

        def _finish_hide() -> None:
            self._w_interp.remove_class("visible")
            if was_fullscreen:
                self._w_interp.remove_class("fullscreen")
                self._w_interp.styles.height = self._panel_height_cells()
                self._screen.query_one(
                    "#main-area"
                ).display = self._prev_main_area_display
                self._w_status.display = self._prev_status_display
            if sync_layout:
                sync_layout()
            if fit_height:
                fit_height()
            update_phase_ui()

        if self._screen.app.animation_enabled:
            self._w_interp.styles.animate("opacity", 0.0, duration=0.22, easing=EASE)
            self._w_interp.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 2)),
                duration=0.28,
                easing=EASE,
            )
            self._screen.set_timer(0.28, _finish_hide)
        else:
            _finish_hide()

    def run(self, drawn_cards, question, cancelled_flag) -> None:
        """Start streaming interpretation in a background worker."""
        self._screen.run_worker(
            self._stream.run(drawn_cards, question, cancelled_flag),
            exclusive=True,
        )

    def stop(self) -> None:
        self._stream.stop()
        self._streaming = False

    def show_error(self, message: str, update_phase_ui, sync_layout=None, fit_height=None) -> None:
        """Hide dialog and display an error message."""
        self.hide(update_phase_ui, sync_layout=sync_layout, fit_height=fit_height)
        self._w_status.update(Text(message, style=C_RED))
