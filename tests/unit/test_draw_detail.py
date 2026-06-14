"""Unit tests for DetailPanel state and rendering behavior."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from textual.widgets import Static

from nekomata.cli.run import _draw_cards
from nekomata.tui.screens.draw_detail import DetailPanel


class _Preview:
    def __init__(self) -> None:
        self.display = False
        self.children = []
        self.styles = SimpleNamespace(height=None, margin=None, animate=MagicMock())
        self._classes: set[str] = set()
        self.refresh = MagicMock()
        self.mount = MagicMock(side_effect=self.children.append)
        self.remove_children = MagicMock(side_effect=self.children.clear)

    def add_class(self, class_name: str) -> None:
        self._classes.add(class_name)

    def remove_class(self, class_name: str) -> None:
        self._classes.discard(class_name)

    def has_class(self, class_name: str) -> bool:
        return class_name in self._classes


class _Screen:
    def __init__(self, *, stacked=False, animation_enabled=False, render_mode="text") -> None:
        self._detail_stacked = stacked
        self.app = SimpleNamespace(
            animation_enabled=animation_enabled,
            render_mode=render_mode,
            config=SimpleNamespace(lang="en"),
        )
        self.preview = _Preview()
        self.timer = MagicMock()
        self.call_after_refresh = MagicMock(side_effect=lambda callback: callback())
        self.set_timer = MagicMock(return_value=self.timer)

    def query_one(self, selector):
        assert selector == "#card-preview"
        return self.preview


class _Slot:
    def __init__(self, drawn_card=None) -> None:
        self.drawn_card = drawn_card


def _make_panel(**screen_kwargs):
    screen = _Screen(**screen_kwargs)
    panel = DetailPanel(screen)
    panel.cache_widgets()
    return panel, screen


def _drawn_card():
    drawn, _ = _draw_cards("single", seed=42)
    return drawn[0]


def test_cache_widgets_and_entrance_offset():
    panel, screen = _make_panel(stacked=False)
    assert panel._w_preview is screen.preview
    assert panel._entrance_offset == (4, 0)

    panel, _screen = _make_panel(stacked=True)
    assert panel._entrance_offset == (0, 2)


def test_show_displays_preview_fits_height_and_updates_slot():
    panel, screen = _make_panel()
    slot = _Slot(_drawn_card())
    sync_interp = MagicMock()

    with (
        patch("nekomata.tui.screens.draw_detail.animate_entrance") as animate,
        patch.object(panel, "update") as update,
    ):
        panel.show(slot, sync_interp=sync_interp)

    assert panel.visible is True
    sync_interp.assert_called_once()
    assert screen.preview.display is True
    assert screen.preview.styles.height == "1fr"
    assert screen.preview.styles.margin == (0, 0, 0, 0)
    screen.preview.refresh.assert_called_with(layout=True)
    assert screen.preview.has_class("visible")
    animate.assert_called_once()
    update.assert_called_once_with(slot, immediate=True)


def test_hide_cancels_pending_and_finishes_with_center_callback():
    panel, screen = _make_panel()
    panel._visible = True
    panel._w_preview.add_class("visible")
    center_spread = MagicMock()
    sync_interp = MagicMock()

    with (
        patch.object(panel, "_cancel_pending") as cancel,
        patch("nekomata.tui.screens.draw_detail.animate_exit") as animate,
    ):
        panel.hide(sync_interp=sync_interp, center_spread=center_spread)

    assert panel.visible is False
    cancel.assert_called_once()
    sync_interp.assert_called_once()
    callback = animate.call_args.kwargs["callback"]

    callback()

    assert not screen.preview.has_class("visible")
    assert screen.preview.display is False
    center_spread.assert_called_once()
    assert panel._pending_center_spread is None


def test_update_ignores_hidden_empty_or_duplicate_slot():
    panel, _screen = _make_panel()
    dc = _drawn_card()

    panel.update(_Slot(dc))
    assert panel._last_preview_id is None

    panel._visible = True
    panel.update(_Slot(None))
    assert panel._last_preview_id is None

    panel._last_preview_id = f"{dc.card.id}:{dc.is_reversed}"
    with patch.object(panel, "_cancel_pending") as cancel:
        panel.update(_Slot(dc))

    cancel.assert_called_once()


def test_update_applies_immediately_or_schedules_debounce():
    panel, _screen = _make_panel()
    panel._visible = True
    dc = _drawn_card()

    with patch.object(panel, "_apply_update") as apply_update:
        panel.update(_Slot(dc), immediate=True)

    apply_update.assert_called_once_with(dc, f"{dc.card.id}:{dc.is_reversed}")

    with patch.object(panel._update_debounce, "schedule") as schedule:
        panel.update(_Slot(dc), immediate=False)

    schedule.assert_called_once_with(dc, f"{dc.card.id}:{dc.is_reversed}")


def test_cancel_pending_stops_render_and_fade_timers():
    panel, _screen = _make_panel()
    render_timer = MagicMock()
    fadein_timer = MagicMock()
    panel._render_timer = render_timer
    panel._fadein_timer = fadein_timer

    with patch.object(panel._update_debounce, "cancel") as cancel:
        panel._cancel_pending()

    cancel.assert_called_once()
    render_timer.stop.assert_called_once()
    fadein_timer.stop.assert_called_once()
    assert panel._render_timer is None
    assert panel._fadein_timer is None


def test_debounce_callback_applies_only_when_visible():
    panel, _screen = _make_panel()
    dc = _drawn_card()

    with patch.object(panel, "_apply_update") as apply_update:
        panel._on_update_debounce(dc, "id")
        apply_update.assert_not_called()

        panel._visible = True
        panel._on_update_debounce(dc, "id")
        apply_update.assert_called_once_with(dc, "id")


def test_apply_update_uses_animation_when_children_exist():
    panel, screen = _make_panel(animation_enabled=True)
    screen.preview.children.append(object())
    dc = _drawn_card()

    panel._apply_update(dc, "preview")

    assert panel._last_preview_id == "preview"
    screen.preview.styles.animate.assert_called_once()
    assert screen.set_timer.call_count == 2
    assert panel._render_timer is screen.timer
    assert panel._fadein_timer is screen.timer


def test_apply_update_stops_leftover_animation_timers():
    panel, _screen = _make_panel(animation_enabled=False)
    render_timer = MagicMock()
    fadein_timer = MagicMock()
    panel._render_timer = render_timer
    panel._fadein_timer = fadein_timer

    panel._apply_update(_drawn_card(), "preview")

    render_timer.stop.assert_called_once()
    fadein_timer.stop.assert_called_once()


def test_render_slot_uses_full_detail_widgets_when_available():
    panel, screen = _make_panel(render_mode="full")
    dc = _drawn_card()

    with patch(
        "nekomata.tui.screens.draw_detail.render_card_full_detail_widgets", return_value=(Static("img"), "text")
    ):
        panel._render_slot(dc)

    screen.preview.remove_children.assert_called_once()
    assert screen.preview.mount.call_count == 2


def test_render_slot_falls_back_to_text_detail_and_fades_in():
    panel, screen = _make_panel(render_mode="text", animation_enabled=True)
    dc = _drawn_card()

    with patch("nekomata.tui.screens.draw_detail.render_card_detail", return_value="detail") as render:
        panel._render_slot(dc)

    render.assert_called_once_with(dc, lang="en")
    screen.preview.mount.assert_called_once()

    panel._fade_in_preview()

    screen.preview.styles.animate.assert_called_once()
