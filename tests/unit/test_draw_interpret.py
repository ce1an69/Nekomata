"""Unit tests for _compose_copy_text from draw_interpret.py."""

from unittest.mock import MagicMock, patch

from nekomata.cli.run import _draw_cards
from nekomata.tui.screens.draw_interpret import InterpretMixin, _compose_copy_text
from nekomata.tui.screens.draw_messages import StreamDone, StreamError
from nekomata.tui.screens.draw_phase import Phase


class _Harness(InterpretMixin):
    pass


def _make_harness() -> _Harness:
    h = _Harness()
    h.app = MagicMock()
    h.app.config = MagicMock(lang="en")
    h.phase = Phase.DONE
    h._dialog = MagicMock(is_streaming=False, is_visible=True, fullscreen=False)
    h._detail = MagicMock(visible=False)
    h._stream = MagicMock()
    h._stream._content_chars = list("Done")
    h._stream.messages = [{"role": "user", "content": "question"}]
    h._w_interp = MagicMock(max_scroll_y=10, scroll_y=10)
    h._w_interp_content = MagicMock()
    h._w_interp_hints = MagicMock()
    h._w_footer = MagicMock()
    h._w_followup_input = MagicMock(value="", placeholder="")
    h._w_followup_section = MagicMock(display=False)
    h._box = MagicMock(active_box="spread")
    h._followup_active = False
    h._followup_question = ""
    h._followup_remaining = 2
    h._followup_visible = False
    h._prev_interp_content = ""
    h._initial_interp_content = ""
    h._messages_history = []
    h._first_interp_done = False
    h._skip_phase_ui_message = False
    h._question = "Question"
    h._drawn_cards, _ = _draw_cards("single", seed=42)
    h._cancelled = False
    h._pending_flips = 0
    h._w_main_area = MagicMock()
    h._center_spread_area = MagicMock()
    h._sync_interp_layout = MagicMock()
    h._update_phase_ui = MagicMock()
    h._update_footer_fullscreen = MagicMock()
    h._update_followup_hints = MagicMock()
    h.run_worker = MagicMock()
    h.call_after_refresh = MagicMock(side_effect=lambda callback: callback())
    h.query = MagicMock(return_value=[])
    h.set_timer = MagicMock()
    return h


class _FakeSlot:
    def __init__(self, *, revealed: bool = False):
        self.is_revealed = revealed
        self.flip_done_callback = None
        self.focus = MagicMock()
        self.add_class = MagicMock()
        self.remove_class = MagicMock()
        self.set_timer = MagicMock()

    async def flip(self):
        return None


def test_compose_copy_text_with_question_and_cards():
    drawn, _ = _draw_cards("single", seed=42)
    result = _compose_copy_text("Will I find love?", drawn, "Great things ahead.", "en")
    assert "# Will I find love?" in result
    assert "Great things ahead." in result
    # Should contain card entry with status
    assert "- " in result


def test_compose_copy_text_empty_question():
    drawn, _ = _draw_cards("single", seed=42)
    result = _compose_copy_text("", drawn, "Interpretation text.", "en")
    assert "# " not in result
    assert "Interpretation text." in result


def test_compose_copy_text_multiple_cards():
    drawn, _ = _draw_cards("past_present_future", seed=42)
    result = _compose_copy_text("My question", drawn, "The reading says...", "en")
    # Should have 3 card entries (one per drawn card)
    lines = [line for line in result.split("\n") if line.startswith("- ")]
    assert len(lines) == 3


def test_compose_copy_text_zh_lang():
    drawn, _ = _draw_cards("single", seed=42)
    result = _compose_copy_text("测试问题", drawn, "解读内容", "zh")
    assert "测试问题" in result
    assert "解读内容" in result


def test_stream_error_config_goes_to_setup():
    h = _make_harness()

    with patch("nekomata.tui.screens.draw_interpret.go_home") as mock_go_home:
        h._on_stream_error(StreamError("missing key", config_error=True))

    h._dialog.stop.assert_called_once()
    mock_go_home.assert_called_once_with(h)
    pushed = h.app.push_screen.call_args.args[0]
    assert pushed.__class__.__name__ == "SetupScreen"
    h.app.notify.assert_called_once_with("missing key", severity="error", timeout=10)


def test_stream_render_resets_combines_followup_and_renders_parts():
    h = _make_harness()

    h._on_stream_render(None)
    h._w_interp_content.update.assert_called_with("")

    h._w_interp_content.update.reset_mock()
    h._followup_active = True
    h._prev_interp_content = "Initial"
    h._followup_question = "Clarify?"
    h._on_stream_render(["part"])
    combined = h._w_interp_content.update.call_args.args[0]
    assert combined.__class__.__name__ == "Group"

    h._w_interp_content.update.reset_mock()
    h._followup_active = False
    h._on_stream_render(["part"])
    rendered = h._w_interp_content.update.call_args.args[0]
    assert rendered.__class__.__name__ == "Group"


def test_stream_hints_and_scroll_near_bottom():
    h = _make_harness()

    h._on_stream_hints("hint")
    h._w_interp_hints.update.assert_called_once_with("hint")

    h._w_interp.max_scroll_y = 12
    h._w_interp.scroll_y = 10
    h._on_stream_scroll()
    h._w_interp.scroll_end.assert_called_once_with(animate=False)


def test_stream_scroll_ignores_when_not_near_bottom():
    h = _make_harness()
    h._w_interp.max_scroll_y = 50
    h._w_interp.scroll_y = 10

    h._on_stream_scroll()

    h._w_interp.scroll_end.assert_not_called()


def test_timer_properties_expose_stream_timers():
    h = _make_harness()
    h._stream._loading_timer = "loading"
    h._stream._timer = "stream"

    assert h._loading_timer == "loading"
    assert h._stream_timer == "stream"


def test_phase_changed_can_skip_or_update_phase_ui():
    from nekomata.tui.screens.draw_messages import PhaseChanged

    h = _make_harness()
    h._skip_phase_ui_message = True

    h._on_phase_changed(PhaseChanged(Phase.PICK, Phase.FLIP))

    assert h._skip_phase_ui_message is False
    h._update_phase_ui.assert_not_called()

    h._on_phase_changed(PhaseChanged(Phase.FLIP, Phase.DONE))

    h._update_phase_ui.assert_called_once_with(Phase.DONE)


def test_box_changed_syncs_or_clears_interp_hints():
    h = _make_harness()
    h._sync_interp_hints = MagicMock()
    h._box.active_box = "interp"

    h._on_box_changed()
    h._sync_interp_hints.assert_called_once()

    h._box.active_box = "spread"
    h._on_box_changed()
    h._w_interp_hints.update.assert_called_once_with("")


def test_sync_interp_hints_for_done_states():
    h = _make_harness()
    h._dialog.is_streaming = True
    h._sync_interp_hints()
    h._w_interp_hints.update.assert_not_called()

    h._dialog.is_streaming = False
    h._first_interp_done = True
    h._sync_interp_hints()
    h._update_followup_hints.assert_called_once()

    h = _make_harness()
    h._first_interp_done = False
    h._sync_interp_hints()
    h._w_interp_hints.update.assert_called_once_with("")
    h._update_footer_fullscreen.assert_called_once()


def test_update_followup_hints_only_after_finished_initial_reading():
    h = _make_harness()
    h._dialog.is_streaming = True
    h._first_interp_done = True

    InterpretMixin._update_followup_hints(h)
    h._w_interp_hints.update.assert_not_called()

    h = _make_harness()
    h._dialog.is_streaming = False
    h._first_interp_done = False
    InterpretMixin._update_followup_hints(h)
    h._w_interp_hints.update.assert_not_called()

    h = _make_harness()
    h._dialog.is_streaming = False
    h._first_interp_done = True
    InterpretMixin._update_followup_hints(h)
    h._w_interp_hints.update.assert_called_once_with("")
    h._update_footer_fullscreen.assert_called_once()


def test_stream_error_non_config_hides_dialog():
    h = _make_harness()

    h._on_stream_error(StreamError("temporary failure", config_error=False))

    h._dialog.hide.assert_called_once_with(h._update_phase_ui, sync_layout=h._sync_interp_layout)
    h.app.push_screen.assert_not_called()
    h.app.notify.assert_called_once_with("temporary failure", severity="error", timeout=10)


def test_stream_done_initial_interpretation_records_history_and_scrolls():
    h = _make_harness()

    h._on_stream_done(StreamDone())

    assert h._prev_interp_content == "Done"
    assert h._initial_interp_content == "Done"
    assert h._messages_history == [
        {"role": "user", "content": "question"},
        {"role": "assistant", "content": "Done"},
    ]
    assert h._first_interp_done is True
    h._dialog.set_streaming.assert_called_once_with(False)
    h._update_followup_hints.assert_called_once()
    h.call_after_refresh.assert_called_once()
    h._w_interp.scroll_end.assert_called_once_with(animate=False)


def test_stream_done_followup_appends_to_previous_content():
    h = _make_harness()
    h._followup_active = True
    h._followup_question = "Clarify?"
    h._prev_interp_content = "Initial"
    h._messages_history = [{"role": "assistant", "content": "Initial"}]

    h._on_stream_done(StreamDone())

    assert h._followup_active is False
    assert "> Clarify?" in h._prev_interp_content
    assert h._prev_interp_content.endswith("Done")
    assert h._messages_history[-1] == {"role": "assistant", "content": "Done"}
    h._w_interp_content.update.assert_called_once()


def test_available_boxes_follow_phase_and_visibility():
    h = _make_harness()

    h.phase = Phase.PICK
    assert h._available_boxes() == ["deck"]

    h.phase = Phase.FLIP
    assert h._available_boxes() == ["spread"]

    h.phase = Phase.DONE
    h._detail.visible = True
    h._dialog.is_visible = True
    assert h._available_boxes() == ["spread", "detail", "interp"]

    h._dialog.fullscreen = True
    assert h._available_boxes() == ["detail", "interp"]

    h._detail.visible = False
    h._dialog.is_visible = False
    assert h._available_boxes() == ["interp"]


def test_action_interpret_shows_dialog_and_starts_stream():
    h = _make_harness()

    h.action_interpret()

    h._dialog.show.assert_called_once_with(sync_layout=h._sync_interp_layout)
    h._dialog.run.assert_called_once()
    assert h._cancelled is False


async def test_spread_slot_flipped_ignores_non_flip_phase():
    h = _make_harness()
    h.phase = Phase.PICK
    event = MagicMock()

    await h.on_spread_slot_flipped(event)

    event.stop.assert_not_called()
    h.run_worker.assert_not_called()


async def test_spread_slot_flipped_focuses_next_slot_and_runs_worker():
    h = _make_harness()
    h.phase = Phase.FLIP
    event = MagicMock()
    event.slot = _FakeSlot(revealed=False)
    next_slot = _FakeSlot(revealed=False)
    h.query.return_value = [event.slot, next_slot]

    await h.on_spread_slot_flipped(event)

    event.stop.assert_called_once()
    next_slot.focus.assert_called_once()
    assert event.slot.flip_done_callback == h._on_flip_done
    assert h._pending_flips == 1
    h.run_worker.assert_called_once()
    h.run_worker.call_args.args[0].close()


def test_flip_done_waits_for_pending_or_non_flip_phase():
    h = _make_harness()
    h.phase = Phase.FLIP
    h._pending_flips = 2

    h._on_flip_done(_FakeSlot())

    assert h._pending_flips == 1
    h._update_phase_ui.assert_not_called()

    h.phase = Phase.PICK
    h._pending_flips = 0
    h._on_flip_done(_FakeSlot())
    h._update_phase_ui.assert_not_called()


def test_flip_done_updates_phase_ui_when_some_slots_unrevealed():
    h = _make_harness()
    h.phase = Phase.FLIP
    h._pending_flips = 0
    h.query.return_value = [_FakeSlot(revealed=True), _FakeSlot(revealed=False)]

    h._on_flip_done(_FakeSlot())

    h._update_phase_ui.assert_called_once()


def test_flip_done_enters_done_phase_and_shows_detail():
    h = _make_harness()
    h.phase = Phase.FLIP
    h._pending_flips = 0
    h.app.animation_enabled = False
    slots = [_FakeSlot(revealed=True), _FakeSlot(revealed=True)]
    h.query.return_value = slots

    h._on_flip_done(slots[0])

    assert h.phase == Phase.DONE
    assert h._box.active_box == "spread"
    h._box.update_highlights.assert_called_once()
    h._detail.show.assert_called_once_with(slots[0], sync_interp=h._sync_interp_layout)
    slots[0].add_class.assert_called_once_with("selected")
    slots[0].focus.assert_called_once()


async def test_spread_slot_selected_ignores_until_done_then_updates_detail():
    h = _make_harness()
    event = MagicMock()
    event.slot = _FakeSlot(revealed=True)
    h.phase = Phase.FLIP

    await h.on_spread_slot_selected(event)
    event.stop.assert_not_called()

    h.phase = Phase.DONE
    other = _FakeSlot(revealed=True)
    h.query.return_value = [other, event.slot]
    await h.on_spread_slot_selected(event)

    event.stop.assert_called_once()
    other.remove_class.assert_called_once_with("selected")
    event.slot.add_class.assert_called_once_with("selected")
    h._detail.update.assert_called_once_with(event.slot)


async def test_completion_shimmer_and_pulse_slot():
    h = _make_harness()
    h.app.animation_enabled = False
    await h._completion_shimmer([_FakeSlot()])
    h.set_timer.assert_not_called()

    h.app.animation_enabled = True
    slot = _FakeSlot()
    with patch("nekomata.tui.screens.draw_interpret.asyncio.sleep") as sleep:
        await h._completion_shimmer([slot])

    h.set_timer.assert_called_once()
    sleep.assert_awaited_once()

    h._pulse_slot(slot)
    slot.add_class.assert_called_once_with("glow")
    slot.set_timer.assert_called_once()


def test_toggle_detail_ignores_non_done_and_hides_visible_detail():
    h = _make_harness()
    h.phase = Phase.PICK
    h.action_toggle_detail()
    h._detail.hide.assert_not_called()

    h.phase = Phase.DONE
    h._detail.visible = True
    h._box.active_box = "detail"
    h._dialog.fullscreen = False
    h.action_toggle_detail()

    assert h._box.active_box == "spread"
    h._box.focus_widget.assert_called_once()
    h._detail.hide.assert_called_once_with(sync_interp=h._sync_interp_layout, center_spread=h._center_spread_area)


def test_toggle_detail_shows_hidden_detail_and_updates_first_slot():
    h = _make_harness()
    h.phase = Phase.DONE
    h._detail.visible = False
    h._dialog.fullscreen = False
    slot = _FakeSlot(revealed=True)
    h.query.return_value = [slot]

    h.action_toggle_detail()

    h._detail.show.assert_called_once_with(sync_interp=h._sync_interp_layout)
    h._detail.update.assert_called_once_with(slot, immediate=True)
    slot.focus.assert_called_once()
    h._update_phase_ui.assert_called_once()


def test_toggle_detail_fullscreen_moves_box_to_detail():
    h = _make_harness()
    h.phase = Phase.DONE
    h._detail.visible = False
    h._dialog.fullscreen = True
    h.query.return_value = []

    h.action_toggle_detail()

    assert h._box.active_box == "detail"
    h._box.update_highlights.assert_called_once()
    h._box.focus_widget.assert_called_once()


def test_key_c_copies_initial_interpretation_text():
    h = _make_harness()
    h._first_interp_done = True
    h._initial_interp_content = "Reading text"
    event = MagicMock()

    with patch("nekomata.tui.screens.draw_interpret._copy_text_to_clipboard", return_value=True) as mock_copy:
        h.key_c(event)

    event.stop.assert_called_once()
    copied = mock_copy.call_args.args[0]
    assert "# Question" in copied
    assert "Reading text" in copied
    h.app.notify.assert_called_once()


def test_action_handle_back_toggles_fullscreen_before_confirming_exit():
    h = _make_harness()
    h._dialog.fullscreen = True

    h.action_handle_back()

    h._dialog.toggle_fullscreen.assert_called_once_with(h._w_main_area)
    h.app.push_screen.assert_not_called()


def test_action_handle_back_pushes_confirm_for_visible_dialog():
    h = _make_harness()

    h.action_handle_back()

    pushed = h.app.push_screen.call_args.args[0]
    callback = h.app.push_screen.call_args.kwargs["callback"]
    assert pushed.__class__.__name__ == "ConfirmExitInterpretation"

    callback(True)

    assert h._cancelled is True
    h._dialog.stop.assert_called_once()


def test_key_f_toggles_followup_when_available():
    h = _make_harness()
    h._first_interp_done = True
    event = MagicMock()

    with patch("nekomata.tui.screens.draw_interpret.animate_entrance") as animate:
        h.key_f(event)

    event.stop.assert_called_once()
    assert h._followup_visible is True
    assert h._w_followup_input.value == ""
    assert h._w_followup_section.display is True
    h._w_followup_section.add_class.assert_called_once_with("visible")
    h._sync_interp_layout.assert_called_once()
    animate.assert_called_once()
    h._w_followup_input.focus.assert_called_once()


def test_key_f_ignores_when_no_remaining_followups():
    h = _make_harness()
    h._followup_remaining = 0
    event = MagicMock()

    h.key_f(event)

    event.stop.assert_not_called()
    h._w_followup_section.add_class.assert_not_called()


def test_hide_followup_finishes_with_animation_callback():
    h = _make_harness()
    h._followup_visible = True

    with patch("nekomata.tui.screens.draw_interpret.animate_exit") as animate:
        h._hide_followup()

    assert h._followup_visible is False
    h._sync_interp_layout.assert_called_once()
    callback = animate.call_args.kwargs["callback"]

    callback()

    h._w_followup_section.remove_class.assert_called_once_with("visible")
    assert h._w_followup_section.display is False


def test_followup_submit_ignores_other_inputs_and_empty_question():
    h = _make_harness()
    event = MagicMock()
    event.input.id = "other-input"
    event.value = "Question"

    h.on_input_submitted(event)

    event.stop.assert_not_called()
    h._stream.run_followup.assert_not_called()

    event.input.id = "followup-input"
    event.value = "   "
    h.on_input_submitted(event)

    event.stop.assert_called_once()
    h._stream.run_followup.assert_not_called()


def test_followup_submit_starts_followup_stream():
    h = _make_harness()
    h._messages_history = [{"role": "assistant", "content": "Initial"}]
    event = MagicMock()
    event.input.id = "followup-input"
    event.value = "  Clarify this  "

    with patch("nekomata.tui.screens.draw_interpret.animate_exit"):
        h.on_input_submitted(event)

    assert h._followup_remaining == 1
    assert h._followup_question == "Clarify this"
    assert h._followup_active is True
    h._dialog.set_streaming.assert_called_once_with(True)
    h._stream.reset.assert_called_once_with(append=True)
    h._stream.run_followup.assert_called_once()


def test_key_h_toggles_fullscreen_and_updates_hints():
    h = _make_harness()
    event = MagicMock()

    h.key_h(event)

    event.stop.assert_called_once()
    h._dialog.toggle_fullscreen.assert_called_once_with(h._w_main_area)
    h._update_followup_hints.assert_called_once()
    h._update_footer_fullscreen.assert_called_once()


def test_key_h_ignores_when_dialog_hidden():
    h = _make_harness()
    h._dialog.is_visible = False
    event = MagicMock()

    h.key_h(event)

    event.stop.assert_not_called()
    h._dialog.toggle_fullscreen.assert_not_called()


def test_key_c_reports_copy_failure():
    h = _make_harness()
    h._first_interp_done = True
    h._initial_interp_content = "Reading text"
    event = MagicMock()

    with patch("nekomata.tui.screens.draw_interpret._copy_text_to_clipboard", return_value=False):
        h.key_c(event)

    event.stop.assert_called_once()
    assert h.app.notify.call_args.kwargs["severity"] == "error"


def test_key_c_ignores_without_content_or_while_streaming():
    h = _make_harness()
    h._first_interp_done = True
    h._initial_interp_content = ""
    event = MagicMock()

    h.key_c(event)

    event.stop.assert_called_once()
    h.app.notify.assert_not_called()

    h = _make_harness()
    h._first_interp_done = True
    h._dialog.is_streaming = True
    event = MagicMock()

    h.key_c(event)

    event.stop.assert_not_called()


def test_key_e_starts_export_worker():
    h = _make_harness()
    h._first_interp_done = True
    h._initial_interp_content = "Reading text"
    event = MagicMock()

    h.key_e(event)

    event.stop.assert_called_once()
    h.run_worker.assert_called_once()
    assert h.run_worker.call_args.kwargs["exclusive"] is True

    # Close the coroutine created by key_e so the test does not leak it.
    h.run_worker.call_args.args[0].close()


def test_key_e_ignores_without_content_or_while_streaming():
    h = _make_harness()
    h._first_interp_done = True
    h._initial_interp_content = ""
    event = MagicMock()

    h.key_e(event)

    event.stop.assert_called_once()
    h.run_worker.assert_not_called()

    h = _make_harness()
    h._first_interp_done = True
    h._dialog.is_streaming = True
    event = MagicMock()

    h.key_e(event)

    event.stop.assert_not_called()


async def test_export_image_success_removes_temp_file_and_notifies():
    h = _make_harness()
    h._initial_interp_content = "Reading text"

    with (
        patch("nekomata.tui.screens.draw_interpret.render_interp_image", return_value=object()) as render,
        patch("nekomata.tui.screens.draw_interpret._save_tmp_image", return_value="/tmp/nekomata-test.png") as save,
        patch("nekomata.tui.screens.draw_interpret._copy_image_to_clipboard", return_value=True) as copy,
        patch("nekomata.tui.screens.draw_interpret.os.unlink") as unlink,
    ):
        await h._export_image()

    render.assert_called_once()
    save.assert_called_once()
    copy.assert_called_once_with("/tmp/nekomata-test.png")
    unlink.assert_called_once_with("/tmp/nekomata-test.png")
    assert h.app.notify.call_args.kwargs["severity"] == "information"


async def test_export_image_failure_still_cleans_up_temp_file():
    h = _make_harness()
    h._initial_interp_content = "Reading text"

    with (
        patch("nekomata.tui.screens.draw_interpret.render_interp_image", return_value=object()),
        patch("nekomata.tui.screens.draw_interpret._save_tmp_image", return_value="/tmp/nekomata-test.png"),
        patch("nekomata.tui.screens.draw_interpret._copy_image_to_clipboard", side_effect=RuntimeError("copy failed")),
        patch("nekomata.tui.screens.draw_interpret.os.unlink", side_effect=OSError("already gone")) as unlink,
    ):
        await h._export_image()

    unlink.assert_called_once_with("/tmp/nekomata-test.png")
    assert h.app.notify.call_args.kwargs["severity"] == "error"


def test_action_handle_back_hides_followup_first():
    h = _make_harness()
    h._followup_visible = True

    with patch("nekomata.tui.screens.draw_interpret.animate_exit"):
        h.action_handle_back()

    assert h._followup_visible is False
    h.app.push_screen.assert_not_called()


def test_action_handle_back_toggles_detail_when_dialog_hidden():
    h = _make_harness()
    h._dialog.is_visible = False
    h._detail.visible = True
    h.action_toggle_detail = MagicMock()

    h.action_handle_back()

    h.action_toggle_detail.assert_called_once()


def test_action_handle_back_goes_home_when_no_layers_remain():
    h = _make_harness()
    h._dialog.is_visible = False
    h._detail.visible = False

    with patch("nekomata.tui.screens.draw_interpret.go_home") as mock_go_home:
        h.action_handle_back()

    mock_go_home.assert_called_once_with(h)


def test_action_handle_back_confirm_cancel_keeps_streaming():
    h = _make_harness()

    h.action_handle_back()
    callback = h.app.push_screen.call_args.kwargs["callback"]
    callback(False)

    assert h._cancelled is False
    h._dialog.stop.assert_not_called()
