"""Unit tests for draw screen widget behavior."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from textual.widgets import Static

from nekomata.cli.run import _draw_cards
from nekomata.tui.screens.draw_widgets import ConfirmExitInterpretation, DeckCard, SpreadSlot


def _drawn_card():
    drawn, _ = _draw_cards("single", seed=42)
    return drawn[0]


def test_confirm_exit_actions_dismiss_with_expected_value():
    screen = ConfirmExitInterpretation()
    screen.dismiss = MagicMock()

    screen.action_confirm()
    screen.action_cancel()

    screen.dismiss.assert_any_call(True)
    screen.dismiss.assert_any_call(False)


def test_confirm_exit_mount_animates_card():
    screen = ConfirmExitInterpretation()
    card = MagicMock()
    screen.query_one = MagicMock(return_value=card)

    with patch("nekomata.tui.screens.draw_widgets.animate_entrance") as animate:
        screen.on_mount()

    animate.assert_called_once()


def test_deck_card_pick_posts_once_and_ignores_picked_card():
    card = DeckCard(3)
    card.post_message = MagicMock()
    card.has_class = MagicMock(return_value=False)

    card.on_click()

    message = card.post_message.call_args.args[0]
    assert message.card is card

    card.post_message.reset_mock()
    card.has_class.return_value = True
    card.key_enter()

    card.post_message.assert_not_called()


class _TestSpreadSlot(SpreadSlot):
    def __init__(self, position_index: int, position_name_zh: str, app, styles) -> None:
        self._test_app = app
        self._test_styles = styles
        self._test_children = []
        self._test_label = SimpleNamespace(display=True, update=MagicMock())
        super().__init__(position_index, position_name_zh)
        self._test_styles = styles
        self.post_message = MagicMock()
        self.mount = MagicMock(side_effect=self._test_children.append)

    @property
    def app(self):
        return self._test_app

    @property
    def styles(self):
        return self._test_styles

    @styles.setter
    def styles(self, value):
        self._test_styles = value

    @property
    def children(self):
        return self._test_children

    @children.setter
    def children(self, value):
        self._test_children = value

    def query_one(self, *args, **kwargs):
        return self._test_label


def _slot(*, animation_enabled=False, render_mode="text"):
    app = SimpleNamespace(
        animation_enabled=animation_enabled,
        render_mode=render_mode,
        config=SimpleNamespace(lang="en"),
        update_styles=MagicMock(),
    )
    styles = SimpleNamespace(opacity=1, offset=(0, 0), animate=MagicMock())
    return _TestSpreadSlot(0, "Past", app, styles)


def test_build_reveal_content_returns_none_without_drawn_card():
    slot = _slot()
    assert slot._build_reveal_content() is None


def test_build_reveal_content_uses_image_widget_when_available():
    slot = _slot(render_mode="full")
    slot.drawn_card = _drawn_card()
    image = Static("image")

    with patch("nekomata.tui.screens.draw_widgets.create_card_face_widget", return_value=image):
        assert slot._build_reveal_content() is image


def test_build_reveal_content_falls_back_to_panel():
    slot = _slot(render_mode="text")
    slot.drawn_card = _drawn_card()

    panel = slot._build_reveal_content()

    assert panel.__class__.__name__ == "Panel"


def test_place_card_mounts_widget_reveal_and_updates_label():
    slot = _slot(render_mode="full")
    dc = _drawn_card()
    reveal = Static("image")

    with (
        patch.object(slot, "remove_class") as remove_class,
        patch.object(slot, "add_class") as add_class,
        patch.object(slot, "_build_reveal_content", return_value=reveal),
    ):
        slot.place_card(dc)

    assert slot.drawn_card is dc
    remove_class.assert_called_once_with("empty")
    add_class.assert_called_once_with("face-down")
    assert reveal.display is False
    slot.mount.assert_called_once_with(reveal)
    slot._test_label.update.assert_called_once()


def test_place_card_mounts_static_reveal_for_renderable_panel():
    slot = _slot(render_mode="text")
    dc = _drawn_card()

    with patch.object(slot, "_build_reveal_content", return_value="renderable"):
        slot.place_card(dc)

    mounted = slot.mount.call_args.args[0]
    assert isinstance(mounted, Static)
    assert mounted.display is False


def test_render_revealed_toggles_reversed_and_shows_child():
    slot = _slot()
    dc = _drawn_card()
    dc = type(dc)(card=dc.card, position=dc.position, is_reversed=True)
    slot.drawn_card = dc
    reveal = MagicMock(display=False)
    reveal.has_class.return_value = False
    slot.children = [MagicMock(), reveal]
    slot.children[0].has_class.return_value = True

    with patch.object(slot, "add_class") as add_class:
        slot._render_revealed()

    add_class.assert_called_once_with("reversed")
    assert reveal.display is True


def test_render_revealed_returns_without_drawn_card():
    slot = _slot()

    with patch.object(slot, "query_one") as query_one:
        slot._render_revealed()

    query_one.assert_not_called()


def test_show_revealed_state_marks_slot_revealed():
    slot = _slot()
    slot.drawn_card = _drawn_card()

    with (
        patch.object(slot, "remove_class") as remove_class,
        patch.object(slot, "add_class") as add_class,
        patch.object(slot, "_render_revealed") as render,
    ):
        slot._show_revealed_state()

    assert slot.is_revealed is True
    remove_class.assert_called_once_with("face-down")
    add_class.assert_called_once_with("revealed")
    render.assert_called_once()


async def test_flip_without_animation_reveals_and_calls_callback():
    slot = _slot(animation_enabled=False)
    slot.drawn_card = _drawn_card()
    callback = MagicMock()
    slot.flip_done_callback = callback

    with patch.object(slot, "_show_revealed_state") as show:
        await slot.flip()

    show.assert_called_once()
    assert slot.styles.opacity == 1
    assert slot.styles.offset == (0, 0)
    assert slot._flipping is False
    callback.assert_called_once_with(slot)


async def test_flip_with_animation_runs_animation_sequence():
    slot = _slot(animation_enabled=True)
    slot.drawn_card = _drawn_card()
    callback = MagicMock()
    slot.flip_done_callback = callback

    with (
        patch("nekomata.tui.screens.draw_widgets.asyncio.sleep") as sleep,
        patch.object(slot, "_show_revealed_state") as show,
        patch.object(slot, "add_class") as add_class,
        patch.object(slot, "remove_class") as remove_class,
    ):
        await slot.flip()

    assert slot.styles.animate.call_count == 4
    assert sleep.await_count == 3
    show.assert_called_once()
    add_class.assert_called_once_with("glow")
    remove_class.assert_called_once_with("glow")
    callback.assert_called_once_with(slot)
    assert slot._flipping is False


def test_activate_posts_flipped_or_selected_messages():
    slot = _slot()
    slot.drawn_card = _drawn_card()

    slot.on_click()

    message = slot.post_message.call_args.args[0]
    assert message.__class__.__name__ == "Flipped"
    assert slot._flipping is True

    slot.post_message.reset_mock()
    slot.key_enter()
    slot.post_message.assert_not_called()

    slot.is_revealed = True
    slot._flipping = False
    slot.key_enter()
    message = slot.post_message.call_args.args[0]
    assert message.__class__.__name__ == "Selected"


def test_focus_posts_selected_for_revealed_slot_only():
    slot = _slot()

    slot.on_focus()
    slot.post_message.assert_not_called()

    slot.is_revealed = True
    slot.on_focus()
    assert slot.post_message.call_args.args[0].__class__.__name__ == "Selected"
