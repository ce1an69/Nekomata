"""Interpretation dialog manager for the draw screen."""

from nekomata.core.render.styles import EASE
from nekomata.tui.render.animations import animate_entrance, animate_exit
from nekomata.tui.screens.draw_constants import (
    INTERP_FULLSCREEN_VERTICAL_CHROME,
    INTERP_MAX_HEIGHT,
    INTERP_MIN_HEIGHT,
    INTERP_PANEL_HEIGHT_RATIO,
)
from nekomata.tui.screens.draw_messages import DetailHideRequested, DetailShowRequested
from nekomata.tui.screens.stream_handler import StreamHandler


class InterpretationDialog:
    """Manages the interpretation dialog: show/hide, layout, streaming.

    Communicates with DetailPanel via Messages (DetailShowRequested /
    DetailHideRequested) instead of directly accessing ``screen._detail``.
    """

    def __init__(
        self,
        screen,
        box_manager,
        stream: StreamHandler,
        get_detail_visible,
    ) -> None:
        self._screen = screen
        self._box = box_manager
        self._stream = stream
        self._get_detail_visible = get_detail_visible
        self._streaming = False
        self._fullscreen = False
        self._prev_detail_visible = False
        self._prev_main_area_display = True
        self._height_timers: list = []
        # Cache widget references (set after mount)
        self._w_interp = None
        self._w_content = None
        self._w_hints = None

    def cache_widgets(self) -> None:
        self._w_interp = self._screen.query_one("#interp-dialog")
        self._w_content = self._screen.query_one("#interp-dialog-content")
        self._w_hints = self._screen.query_one("#interp-dialog-hints")

    @property
    def is_visible(self) -> bool:
        return self._w_interp.has_class("visible")

    @property
    def is_streaming(self) -> bool:
        return self._streaming

    def set_streaming(self, value: bool) -> None:
        self._streaming = value

    # -- Layout --

    @property
    def fullscreen(self) -> bool:
        return self._fullscreen

    def toggle_fullscreen(self, main_area) -> None:
        """Toggle fullscreen mode: hide spread, keep detail available."""
        self._fullscreen = not self._fullscreen
        spread_area = self._screen.query_one("#spread-area")
        detail_visible = self._get_detail_visible()
        if self._fullscreen:
            self._prev_detail_visible = detail_visible
            self._prev_main_area_display = main_area.display
            fullscreen_height = self._fullscreen_height_cells()
            spread_area.display = False
            main_area.display = False
            self._start_height_fullscreen(fullscreen_height)
        else:
            current_height = self._w_interp.region.height
            self._restore_fullscreen_layout(spread_area, main_area)
            self._animate_interp_height(
                current_height,
                self._panel_height_cells(),
                on_complete=self._finish_fullscreen_exit,
            )

    def _start_height_fullscreen(self, height: int) -> None:
        self._w_interp.add_class("fullscreen")
        self._cancel_height_anim()
        detail_visible = self._get_detail_visible()
        self.sync_layout(detail_visible, self._screen.size.width)
        self._w_interp.styles.height = height

    def _fullscreen_height_cells(self) -> int:
        reading_area = self._screen.query_one("#reading-area")
        height = reading_area.region.height
        if height <= 0:
            height = self._screen.size.height - INTERP_FULLSCREEN_VERTICAL_CHROME
        return max(INTERP_MIN_HEIGHT, height)

    def _restore_fullscreen_layout(self, spread_area, main_area) -> None:
        """Restore normal flow before shrinking the fullscreen dialog."""
        main_area.display = self._prev_main_area_display
        spread_area.display = True
        detail_visible = self._get_detail_visible()
        if self._prev_detail_visible and not detail_visible:
            self._screen.post_message(
                DetailShowRequested(slot=None),
            )
            # sync_layout will be called by the DetailShowRequested handler
        elif not self._prev_detail_visible and detail_visible:
            self._screen.post_message(DetailHideRequested(center_spread=None))
            # sync_layout will be called by the DetailHideRequested handler
        else:
            self.sync_layout(detail_visible, self._screen.size.width)

    def _finish_fullscreen_exit(self) -> None:
        """Finish returning the interpretation dialog to its normal panel."""
        self._w_interp.remove_class("fullscreen")
        self._w_interp.styles.height = self._panel_height_cells()

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

    def _animate_interp_height(self, from_height: int, to_height: int, on_complete=None) -> None:
        """Animate interp dialog height using Textual's native animation."""
        self._cancel_height_anim()
        if not self._screen.app.animation_enabled:
            self._w_interp.styles.height = to_height
            if on_complete:
                on_complete()
            return
        self._w_interp.styles.height = from_height
        duration = 0.28
        self._w_interp.styles.animate("height", to_height, duration=duration, easing="out_cubic")
        if on_complete:
            timer = self._screen.set_timer(duration + 0.01, on_complete)
            self._height_timers.append(timer)

    def sync_layout(self, detail_visible: bool, screen_width: int) -> None:
        """Keep interp spacing in sync with the surrounding reading layout."""
        if detail_visible:
            self._w_interp.add_class("detail-visible")
        else:
            self._w_interp.remove_class("detail-visible")
        self._w_interp.styles.margin = (0, 1, 0, 1)
        self._w_interp.styles.width = "1fr"

    # -- Show / Hide --

    def show(self, sync_layout=None) -> None:
        """Display the interpretation dialog with entrance animation."""
        self.set_streaming(True)
        self._box.active_box = "interp"
        self._box.update_highlights()
        if sync_layout:
            sync_layout()
        self._w_interp.display = True
        self._w_interp.add_class("visible")
        animate_entrance(self._w_interp, duration=0.30, dy=2, easing=EASE)
        self._stream.reset()

    def hide(self, update_phase_ui, sync_layout=None) -> None:
        """Hide the dialog with exit animation, then update phase UI."""
        self.set_streaming(False)
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
                self._screen.query_one("#main-area").display = self._prev_main_area_display
            self._w_interp.styles.height = self._panel_height_cells()
            if sync_layout:
                sync_layout()
            update_phase_ui()

        if self._screen.app.animation_enabled:
            animate_exit(
                self._w_interp,
                duration=0.28,
                dy=2,
                easing=EASE,
                callback=_finish_hide,
            )
        else:
            _finish_hide()

    def run(self, drawn_cards, question, cancelled_flag) -> None:
        """Start streaming interpretation in a background thread worker."""
        self._stream.run(drawn_cards, question, cancelled_flag)

    def stop(self) -> None:
        self._stream.stop()
        self.set_streaming(False)
