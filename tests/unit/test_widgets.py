"""Unit tests for screens/widgets.py helpers."""

from unittest.mock import MagicMock

from nekomata.screens.widgets import focus_sibling


def test_focus_sibling_moves_to_next():
    """focus_sibling with delta=1 moves focus to the next item."""
    screen = MagicMock()
    item_a, item_b, item_c = MagicMock(), MagicMock(), MagicMock()
    screen.query.return_value = [item_a, item_b, item_c]
    screen.focused = item_a

    focus_sibling(screen, MagicMock, 1)
    item_b.focus.assert_called_once()


def test_focus_sibling_moves_to_previous():
    """focus_sibling with delta=-1 moves focus to the previous item."""
    screen = MagicMock()
    item_a, item_b, item_c = MagicMock(), MagicMock(), MagicMock()
    screen.query.return_value = [item_a, item_b, item_c]
    screen.focused = item_c

    focus_sibling(screen, MagicMock, -1)
    item_b.focus.assert_called_once()


def test_focus_sibling_no_wrap_at_end():
    """focus_sibling does not wrap past the last item."""
    screen = MagicMock()
    item_a = MagicMock()
    screen.query.return_value = [item_a]
    screen.focused = item_a

    focus_sibling(screen, MagicMock, 1)
    # Should not call focus on anything — already at the end
    item_a.focus.assert_not_called()


def test_focus_sibling_no_wrap_at_start():
    """focus_sibling does not wrap past the first item."""
    screen = MagicMock()
    item_a = MagicMock()
    screen.query.return_value = [item_a]
    screen.focused = item_a

    focus_sibling(screen, MagicMock, -1)
    item_a.focus.assert_not_called()


def test_focus_sibling_empty_list():
    """focus_sibling does nothing when no items are found."""
    screen = MagicMock()
    screen.query.return_value = []
    # Should not raise
    focus_sibling(screen, MagicMock, 1)


def test_focus_sibling_unfocused_falls_back_to_first():
    """If focused widget is not in the list, focus the first item."""
    screen = MagicMock()
    item_a, item_b = MagicMock(), MagicMock()
    screen.query.return_value = [item_a, item_b]
    screen.focused = "something_else"  # not in the list

    focus_sibling(screen, MagicMock, 1)
    item_a.focus.assert_called_once()


def test_focus_sibling_boundary_no_overflow():
    """focus_sibling at last item with +1 does nothing (no wrap)."""
    screen = MagicMock()
    item_a, item_b = MagicMock(), MagicMock()
    screen.query.return_value = [item_a, item_b]
    screen.focused = item_b  # already last

    focus_sibling(screen, MagicMock, 1)
    item_b.focus.assert_not_called()
