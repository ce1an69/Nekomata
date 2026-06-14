"""Unit tests for InterpretationDialog layout and lifecycle."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from textual.geometry import Region, Size

from nekomata.tui.screens.draw_dialog import InterpretationDialog
from nekomata.tui.screens.draw_messages import DetailHideRequested, DetailShowRequested


class _Widget:
    def __init__(self, *, height: int = 12, display=True) -> None:
        self.display = display
        self.region = Region(0, 0, 20, height)
        self.styles = SimpleNamespace(height=None, margin=None, width=None, animate=MagicMock())
        self._classes: set[str] = set()
        self.focus = MagicMock()

    def add_class(self, class_name: str) -> None:
        self._classes.add(class_name)

    def remove_class(self, class_name: str) -> None:
        self._classes.discard(class_name)

    def has_class(self, class_name: str) -> bool:
        return class_name in self._classes


class _Screen:
    def __init__(self, *, animation_enabled: bool = False, reading_height: int = 30) -> None:
        self.size = Size(100, 40)
        self.app = SimpleNamespace(animation_enabled=animation_enabled)
        self.messages = []
        self.timer = MagicMock()
        self.widgets = {
            "#interp-dialog": _Widget(height=14),
            "#interp-dialog-content": _Widget(),
            "#interp-dialog-hints": _Widget(),
            "#spread-area": _Widget(),
            "#main-area": _Widget(display=True),
            "#reading-area": _Widget(height=reading_height),
        }

    def query_one(self, selector):
        return self.widgets[selector]

    def post_message(self, message) -> None:
        self.messages.append(message)

    def set_timer(self, delay, callback):
        self.timer.delay = delay
        self.timer.callback = callback
        return self.timer


def _make_dialog(*, animation_enabled: bool = False, detail_visible=False, reading_height: int = 30):
    screen = _Screen(animation_enabled=animation_enabled, reading_height=reading_height)
    box = MagicMock(active_box="spread")
    stream = MagicMock()
    dialog = InterpretationDialog(screen, box, stream, lambda: detail_visible)
    dialog.cache_widgets()
    return dialog, screen, box, stream


def test_cache_widgets_and_visibility_properties():
    dialog, screen, _box, _stream = _make_dialog()

    assert dialog._w_interp is screen.widgets["#interp-dialog"]
    assert dialog._w_content is screen.widgets["#interp-dialog-content"]
    assert dialog._w_hints is screen.widgets["#interp-dialog-hints"]
    assert dialog.is_visible is False

    dialog._w_interp.add_class("visible")
    assert dialog.is_visible is True

    dialog.set_streaming(True)
    assert dialog.is_streaming is True


def test_toggle_fullscreen_enter_hides_spread_and_main_area():
    dialog, screen, _box, _stream = _make_dialog(detail_visible=True)
    main_area = screen.widgets["#main-area"]

    dialog.toggle_fullscreen(main_area)

    assert dialog.fullscreen is True
    assert dialog._prev_detail_visible is True
    assert screen.widgets["#spread-area"].display is False
    assert main_area.display is False
    assert dialog._w_interp.has_class("fullscreen")
    assert dialog._w_interp.has_class("detail-visible")
    assert dialog._w_interp.styles.height == 30


def test_fullscreen_height_uses_screen_fallback_when_reading_area_has_no_height():
    dialog, _screen, _box, _stream = _make_dialog(reading_height=0)

    assert dialog._fullscreen_height_cells() == 35


def test_toggle_fullscreen_exit_restores_layout_and_finishes_without_animation():
    dialog, screen, _box, _stream = _make_dialog(animation_enabled=False)
    main_area = screen.widgets["#main-area"]
    dialog.toggle_fullscreen(main_area)

    dialog.toggle_fullscreen(main_area)

    assert dialog.fullscreen is False
    assert screen.widgets["#spread-area"].display is True
    assert main_area.display is True
    assert not dialog._w_interp.has_class("fullscreen")
    assert dialog._w_interp.styles.height == dialog._panel_height_cells()


def test_restore_fullscreen_layout_requests_detail_show_when_needed():
    dialog, screen, _box, _stream = _make_dialog(detail_visible=False)
    dialog._prev_detail_visible = True

    dialog._restore_fullscreen_layout(screen.widgets["#spread-area"], screen.widgets["#main-area"])

    assert isinstance(screen.messages[-1], DetailShowRequested)


def test_restore_fullscreen_layout_requests_detail_hide_when_needed():
    dialog, screen, _box, _stream = _make_dialog(detail_visible=True)
    dialog._prev_detail_visible = False

    dialog._restore_fullscreen_layout(screen.widgets["#spread-area"], screen.widgets["#main-area"])

    assert isinstance(screen.messages[-1], DetailHideRequested)


def test_animate_interp_height_enabled_sets_timer_for_completion():
    dialog, screen, _box, _stream = _make_dialog(animation_enabled=True)
    callback = MagicMock()

    dialog._animate_interp_height(5, 12, on_complete=callback)

    assert dialog._w_interp.styles.height == 5
    dialog._w_interp.styles.animate.assert_called_once()
    assert dialog._height_timers == [screen.timer]
    callback.assert_not_called()


def test_cancel_height_anim_stops_and_clears_timers():
    dialog, _screen, _box, _stream = _make_dialog()
    timer = MagicMock()
    dialog._height_timers = [timer]

    dialog._cancel_height_anim()

    timer.stop.assert_called_once()
    assert dialog._height_timers == []


def test_show_sets_interp_active_and_resets_stream():
    dialog, _screen, box, stream = _make_dialog()
    sync_layout = MagicMock()

    with patch("nekomata.tui.screens.draw_dialog.animate_entrance") as animate:
        dialog.show(sync_layout=sync_layout)

    assert dialog.is_streaming is True
    assert box.active_box == "interp"
    box.update_highlights.assert_called_once()
    sync_layout.assert_called_once()
    assert dialog._w_interp.display is True
    assert dialog._w_interp.has_class("visible")
    animate.assert_called_once()
    stream.reset.assert_called_once()


def test_hide_without_animation_finishes_immediately():
    dialog, screen, box, stream = _make_dialog(animation_enabled=False)
    dialog._w_interp.add_class("visible")
    dialog._w_interp.add_class("fullscreen")
    dialog._fullscreen = True
    dialog._prev_main_area_display = True
    update_phase_ui = MagicMock()
    sync_layout = MagicMock()

    dialog.hide(update_phase_ui, sync_layout=sync_layout)

    assert dialog.is_streaming is False
    stream.stop.assert_called_once()
    assert box.active_box == "spread"
    assert not dialog._w_interp.has_class("visible")
    assert not dialog._w_interp.has_class("fullscreen")
    assert screen.widgets["#main-area"].display is True
    sync_layout.assert_called_once()
    update_phase_ui.assert_called_once()


def test_hide_with_animation_passes_finish_callback():
    dialog, _screen, _box, _stream = _make_dialog(animation_enabled=True)
    update_phase_ui = MagicMock()

    with patch("nekomata.tui.screens.draw_dialog.animate_exit") as animate:
        dialog.hide(update_phase_ui)

    callback = animate.call_args.kwargs["callback"]
    update_phase_ui.assert_not_called()

    callback()

    update_phase_ui.assert_called_once()


def test_run_and_stop_delegate_to_stream():
    dialog, _screen, _box, stream = _make_dialog()
    drawn = [MagicMock()]
    cancelled = MagicMock()

    dialog.run(drawn, "question", cancelled)
    dialog.stop()

    stream.run.assert_called_once_with(drawn, "question", cancelled)
    stream.stop.assert_called_once()
    assert dialog.is_streaming is False
