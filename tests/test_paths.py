"""Tests for centralized path resolution."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


class TestDevMode:
    """Path resolution in normal (non-frozen) development mode."""

    def test_base_dir_is_project_root(self):
        from nekomata._paths import base_dir

        result = base_dir()
        assert (result / "data" / "card_meanings.yaml").exists()

    def test_data_dir(self):
        from nekomata._paths import data_dir

        assert data_dir().name == "data"
        assert (data_dir() / "card_meanings.yaml").exists()

    def test_assets_dir(self):
        from nekomata._paths import assets_dir

        assert assets_dir().name == "assets"
        assert (assets_dir() / "cards").is_dir()

    def test_static_dir(self):
        from nekomata._paths import static_dir

        assert static_dir().name == "static"
        assert (static_dir() / "index.html").exists()


class TestFrozenMode:
    """Path resolution in PyInstaller frozen mode."""

    def test_frozen_uses_meipass(self, tmp_path):
        from nekomata import _paths

        fake_root = tmp_path / "frozen_root"
        fake_root.mkdir()
        (fake_root / "data").mkdir()
        (fake_root / "assets").mkdir()
        (fake_root / "static").mkdir()

        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "_MEIPASS", str(fake_root), create=True),
        ):
            assert _paths.base_dir() == fake_root
            assert _paths.data_dir() == fake_root / "data"
            assert _paths.assets_dir() == fake_root / "assets"
            assert _paths.static_dir() == fake_root / "static"

    def test_not_frozen_ignores_meipass(self):
        from nekomata import _paths

        with patch.object(sys, "frozen", False, create=True):
            result = _paths.base_dir()
            # Should resolve to project root, not any fake path
            assert (result / "data" / "card_meanings.yaml").exists()
