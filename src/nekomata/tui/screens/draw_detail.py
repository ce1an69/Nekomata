"""Detail panel manager for the draw screen."""

from textual.widgets import Static

from nekomata.core.render.card_renderer import render_card_detail, render_card_full_detail_widgets
from nekomata.core.render.styles import EASE
from nekomata.tui.render.animations import animate_entrance, animate_exit
from nekomata.tui.screens._debounce import DebouncedCall
from nekomata.tui.screens.draw_constants import (
    DETAIL_UPDATE_DEBOUNCE,
    PANEL_ENTRANCE_DURATION,
    PANEL_EXIT_DURATION,
    PANEL_FADE_IN_DURATION,
    PANEL_FADE_OUT_DURATION,
    PANEL_SWAP_DELAY,
)


class DetailPanel:
    """Manages the card detail side panel: show/hide, content updates."""

    def __init__(self, screen) -> None:
        self._screen = screen
        self._visible = False
        self._last_preview_id: str | None = None
        self._pending_center_spread = None
        # 详情渲染防抖: 快速移动焦点时只渲染最终停留的那一张
        self._update_debounce = DebouncedCall(screen, DETAIL_UPDATE_DEBOUNCE, self._on_update_debounce)
        # _apply_update 内部的动画定时器句柄(用于取消孤立定时器)
        self._render_timer = None
        self._fadein_timer = None
        # Widget reference (set after mount)
        self._w_preview = None

    def cache_widgets(self) -> None:
        self._w_preview = self._screen.query_one("#card-preview")

    @property
    def _entrance_offset(self) -> tuple[int, int]:
        """Animation offset: vertical for stacked layout, horizontal for side-by-side."""
        return (0, 2) if self._screen._detail_stacked else (4, 0)

    @property
    def visible(self) -> bool:
        return self._visible

    # -- Show / Hide --

    def show(self, slot=None, sync_interp=None) -> None:
        """Display the detail panel with entrance animation."""
        self._visible = True
        if sync_interp:
            sync_interp()
        self._w_preview.display = True
        self._fit_height()
        self._screen.call_after_refresh(self._fit_height)
        self._w_preview.add_class("visible")
        dx, dy = self._entrance_offset
        animate_entrance(self._w_preview, duration=PANEL_ENTRANCE_DURATION, dx=dx, dy=dy, easing=EASE)
        self._last_preview_id = None
        if slot is not None:
            self.update(slot, immediate=True)

    def hide(self, sync_interp=None, center_spread=None) -> None:
        """Hide the detail panel with exit animation."""
        self._visible = False
        self._cancel_pending()
        self._pending_center_spread = center_spread
        if sync_interp:
            sync_interp()
        dx, dy = self._entrance_offset
        animate_exit(
            self._w_preview,
            duration=PANEL_EXIT_DURATION,
            dx=dx,
            dy=dy,
            easing=EASE,
            callback=self._finish_hide,
        )

    def _fit_height(self) -> None:
        """Let the shared reading-area flow define the detail panel height."""
        self._w_preview.styles.height = "1fr"
        self._w_preview.styles.margin = (0, 0, 0, 0)
        self._w_preview.refresh(layout=True)

    def _finish_hide(self) -> None:
        """Complete the hide animation: remove panel from layout, then recenter spread."""
        self._w_preview.remove_class("visible")
        self._w_preview.display = False
        self._w_preview.styles.height = "1fr"
        self._w_preview.styles.margin = (0, 0, 0, 0)
        if self._pending_center_spread:
            self._pending_center_spread()
            self._pending_center_spread = None

    # -- Content --

    def update(self, slot, *, immediate: bool = False) -> None:
        """Update the detail panel content for the given spread slot.

        immediate=False（默认）会防抖：键盘快速移动焦点时仅渲染最终停留的牌，
        避免每次焦点变化都重建图片控件导致卡顿。
        """
        if not self._visible or not slot.drawn_card:
            return
        dc = slot.drawn_card
        preview_id = f"{dc.card.id}:{dc.is_reversed}"
        if self._last_preview_id == preview_id:
            self._cancel_pending()
            return

        self._cancel_pending()
        if immediate:
            self._apply_update(dc, preview_id)
        else:
            self._update_debounce.schedule(dc, preview_id)

    def _cancel_pending(self) -> None:
        self._update_debounce.cancel()
        if self._render_timer is not None:
            self._render_timer.stop()
            self._render_timer = None
        if self._fadein_timer is not None:
            self._fadein_timer.stop()
            self._fadein_timer = None

    def _on_update_debounce(self, dc, preview_id: str) -> None:
        if self._visible:
            self._apply_update(dc, preview_id)

    def _apply_update(self, dc, preview_id: str) -> None:
        self._last_preview_id = preview_id
        # Cancel any leftover render/fadein timers from a previous update
        if self._render_timer is not None:
            self._render_timer.stop()
            self._render_timer = None
        if self._fadein_timer is not None:
            self._fadein_timer.stop()
            self._fadein_timer = None
        if self._screen.app.animation_enabled and self._w_preview.children:
            self._w_preview.styles.animate("opacity", 0.0, duration=PANEL_FADE_OUT_DURATION, easing=EASE)
            self._render_timer = self._screen.set_timer(PANEL_FADE_OUT_DURATION, lambda: self._render_slot(dc))
            self._fadein_timer = self._screen.set_timer(PANEL_SWAP_DELAY, self._fade_in_preview)
        else:
            self._render_slot(dc)

    def _render_slot(self, dc) -> None:
        """Render card detail content into the preview panel."""
        self._w_preview.remove_children()
        lang = self._screen.app.config.lang

        if self._screen.app.render_mode != "text":
            result = render_card_full_detail_widgets(dc, lang, upright_image=True)
            if result is not None:
                from textual.containers import Horizontal

                img_widget, text_panel = result
                self._w_preview.mount(Horizontal(img_widget, classes="card-detail-frame"))
                self._w_preview.mount(Static(text_panel))
                return

        self._w_preview.mount(Static(render_card_detail(dc, lang=lang)))

    def _fade_in_preview(self) -> None:
        """Fade the preview panel back in after content swap."""
        self._w_preview.styles.animate("opacity", 1.0, duration=PANEL_FADE_IN_DURATION, easing=EASE)
