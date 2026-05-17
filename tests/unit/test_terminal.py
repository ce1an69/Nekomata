from unittest.mock import patch

from nekomata.render.terminal import get_render_mode


def test_full_mode():
    with patch("nekomata.render.terminal.shutil.get_terminal_size", return_value=(160, 50)):
        assert get_render_mode() == "full"


def test_medium_mode():
    with patch("nekomata.render.terminal.shutil.get_terminal_size", return_value=(120, 40)):
        assert get_render_mode() == "medium"


def test_compact_mode():
    with patch("nekomata.render.terminal.shutil.get_terminal_size", return_value=(80, 24)):
        assert get_render_mode() == "compact"


def test_text_mode():
    with patch("nekomata.render.terminal.shutil.get_terminal_size", return_value=(60, 20)):
        assert get_render_mode() == "text"


def test_medium_mode_borderline():
    with patch("nekomata.render.terminal.shutil.get_terminal_size", return_value=(130, 45)):
        assert get_render_mode() == "medium"


def test_full_mode_exact_threshold():
    with patch("nekomata.render.terminal.shutil.get_terminal_size", return_value=(159, 49)):
        assert get_render_mode() == "medium"


def test_compact_mode_exact_threshold():
    with patch("nekomata.render.terminal.shutil.get_terminal_size", return_value=(79, 23)):
        assert get_render_mode() == "text"
