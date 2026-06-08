"""Unit tests for core/clipboard.py — cross-platform text/image copy."""

from unittest.mock import MagicMock, patch

from nekomata.core.clipboard import copy_image, copy_text


def _ok_proc(*_a, **_kw):
    return MagicMock(returncode=0)


def _fail_proc(*_a, **_kw):
    return MagicMock(returncode=1)


# -- copy_text --


class TestCopyText:
    def test_macos_success(self):
        with (
            patch("nekomata.core.clipboard.platform.system", return_value="Darwin"),
            patch("nekomata.core.clipboard.subprocess.run", _ok_proc),
        ):
            assert copy_text("hello") is True

    def test_macos_failure(self):
        with (
            patch("nekomata.core.clipboard.platform.system", return_value="Darwin"),
            patch("nekomata.core.clipboard.subprocess.run", _fail_proc),
        ):
            assert copy_text("hello") is False

    def test_linux_xclip(self):
        with (
            patch("nekomata.core.clipboard.platform.system", return_value="Linux"),
            patch("nekomata.core.clipboard.shutil.which", return_value="/usr/bin/xclip"),
            patch("nekomata.core.clipboard.subprocess.run", _ok_proc),
        ):
            assert copy_text("hello") is True

    def test_linux_xsel(self):
        with (
            patch("nekomata.core.clipboard.platform.system", return_value="Linux"),
            patch(
                "nekomata.core.clipboard.shutil.which",
                side_effect=lambda c: "/usr/bin/xsel" if c == "xsel" else None,
            ),
            patch("nekomata.core.clipboard.subprocess.run", _ok_proc),
        ):
            assert copy_text("hello") is True

    def test_linux_no_tool(self):
        with (
            patch("nekomata.core.clipboard.platform.system", return_value="Linux"),
            patch("nekomata.core.clipboard.shutil.which", return_value=None),
        ):
            assert copy_text("hello") is False

    def test_windows(self):
        with (
            patch("nekomata.core.clipboard.platform.system", return_value="Windows"),
            patch("nekomata.core.clipboard.subprocess.run", _ok_proc),
        ):
            assert copy_text("hello") is True

    def test_exception_returns_false(self):
        with (
            patch("nekomata.core.clipboard.platform.system", return_value="Darwin"),
            patch("nekomata.core.clipboard.subprocess.run", side_effect=OSError("boom")),
        ):
            assert copy_text("hello") is False


# -- copy_image --


class TestCopyImage:
    def test_macos_success(self):
        with (
            patch("nekomata.core.clipboard.platform.system", return_value="Darwin"),
            patch("nekomata.core.clipboard._copy_image_macos", return_value=True),
        ):
            assert copy_image("/tmp/test.png") is True

    def test_linux_xclip(self):
        with (
            patch("nekomata.core.clipboard.platform.system", return_value="Linux"),
            patch("nekomata.core.clipboard.shutil.which", return_value="/usr/bin/xclip"),
            patch("nekomata.core.clipboard.subprocess.run", _ok_proc),
        ):
            assert copy_image("/tmp/test.png") is True

    def test_linux_no_xclip(self):
        with (
            patch("nekomata.core.clipboard.platform.system", return_value="Linux"),
            patch("nekomata.core.clipboard.shutil.which", return_value=None),
        ):
            assert copy_image("/tmp/test.png") is False

    def test_unhandled_platform(self):
        with patch("nekomata.core.clipboard.platform.system", return_value="Windows"):
            assert copy_image("/tmp/test.png") is False

    def test_exception_returns_false(self):
        with (
            patch("nekomata.core.clipboard.platform.system", return_value="Darwin"),
            patch("nekomata.core.clipboard._copy_image_macos", side_effect=OSError("boom")),
        ):
            assert copy_image("/tmp/test.png") is False

    def test_macos_path_escaping(self):
        """Paths with quotes and backslashes must be escaped in AppleScript."""
        mock_proc = MagicMock(returncode=0)
        with (
            patch("nekomata.core.clipboard.platform.system", return_value="Darwin"),
            patch("nekomata.core.clipboard.subprocess.run", return_value=mock_proc) as mock_run,
        ):
            from nekomata.core.clipboard import _copy_image_macos

            result = _copy_image_macos('/tmp/path with "quotes" and \\backslash\\.png')
            assert result is True
            # Verify the escaping — osascript args are ["osascript", "-e", script]
            args = mock_run.call_args[0][0]
            script_arg = args[2]
            assert '\\"' in script_arg
