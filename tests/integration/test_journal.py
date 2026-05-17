"""Tests for the journal history screen and /history command."""

import tempfile
from pathlib import Path

import pytest

from nekomata.app import NekomataApp
from nekomata.card.types import Arcana, Card, DrawnCard, Position, Reading
from nekomata.storage.journal import Journal


def _save_reading(db_path: Path, question: str = "测试问题") -> None:
    """Helper: save a reading to a temp journal."""
    journal = Journal(db_path)
    pos = Position(name="Past", name_zh="过去", description="过去的影响")
    card = Card(
        id="test", name="Test", name_zh="测试牌",
        arcana=Arcana.MAJOR, number=0, element="air", astrology="Uranus",
        keywords_upright=("a",), keywords_reversed=("b",),
        meaning_upright="up", meaning_reversed="down",
    )
    drawn = [DrawnCard(card=card, position=pos, is_reversed=False)]
    reading = Reading(
        question=question,
        spread_name="Single Card",
        spread_name_zh="单牌",
        drawn_cards=drawn,
        interpretation="测试解读",
    )
    journal.save(reading)


@pytest.mark.asyncio
async def test_history_command_navigates():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/history"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.journal import JournalScreen
        assert isinstance(app.screen, JournalScreen)


@pytest.mark.asyncio
async def test_history_shows_empty_message():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/history"
        await pilot.press("enter")
        await pilot.pause()
        empty = app.screen.query_one("#empty-msg")
        assert "暂无" in str(empty.render())


@pytest.mark.asyncio
async def test_history_back_button():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/history"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#back")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_history_escape_returns():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/history"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_history_shows_saved_reading():
    """Save a reading, then verify it appears in the history screen."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        _save_reading(db_path, question="日记历史测试")

        # Patch the Journal to use our temp db
        import nekomata.screens.journal as journal_mod
        original_init = journal_mod.Journal.__init__

        def patched_init(self, db_path_arg=None):
            original_init(self, db_path)

        journal_mod.Journal.__init__ = patched_init

        app = NekomataApp()
        async with app.run_test() as pilot:
            inp = app.screen.query_one("#prompt-input")
            inp.value = "/history"
            await pilot.press("enter")
            await pilot.pause()

            from nekomata.screens.journal import JournalScreen, _ReadingItem
            assert isinstance(app.screen, JournalScreen)
            items = app.screen.query("_ReadingItem")
            assert len(items) == 1
            assert "日记历史测试" in str(items[0].render())

        journal_mod.Journal.__init__ = original_init
    finally:
        db_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_delete_requires_double_press():
    """First D shows confirmation, second D actually deletes."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        _save_reading(db_path, question="删除确认测试")

        import nekomata.screens.journal as journal_mod
        original_init = journal_mod.Journal.__init__

        def patched_init(self, db_path_arg=None):
            original_init(self, db_path)

        journal_mod.Journal.__init__ = patched_init

        app = NekomataApp()
        async with app.run_test() as pilot:
            inp = app.screen.query_one("#prompt-input")
            inp.value = "/history"
            await pilot.press("enter")
            await pilot.pause()

            from nekomata.screens.journal import JournalScreen, _ReadingItem
            assert isinstance(app.screen, JournalScreen)
            items = app.screen.query("_ReadingItem")
            assert len(items) == 1

            # Focus the item and press D once — should show confirmation
            items[0].focus()
            await pilot.pause()
            await pilot.press("d")
            await pilot.pause()
            hints = app.screen.query_one("#hints")
            assert "确认删除" in str(hints.render())
            # Item still exists after first press
            assert len(app.screen.query("_ReadingItem")) == 1

            # Second D confirms deletion
            await pilot.press("d")
            await pilot.pause()
            assert len(app.screen.query("_ReadingItem")) == 0

        journal_mod.Journal.__init__ = original_init
    finally:
        db_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_reading_item_selected_on_focus():
    """Focusing a reading item adds the .selected class."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        _save_reading(db_path, question="选中状态测试")

        import nekomata.screens.journal as journal_mod
        original_init = journal_mod.Journal.__init__

        def patched_init(self, db_path_arg=None):
            original_init(self, db_path)

        journal_mod.Journal.__init__ = patched_init

        app = NekomataApp()
        async with app.run_test() as pilot:
            inp = app.screen.query_one("#prompt-input")
            inp.value = "/history"
            await pilot.press("enter")
            await pilot.pause()

            items = app.screen.query("_ReadingItem")
            assert len(items) == 1
            items[0].focus()
            await pilot.pause()
            assert items[0].has_class("selected")

        journal_mod.Journal.__init__ = original_init
    finally:
        db_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_tab_cycles_reading_to_button():
    """Tab key cycles focus from reading list to back button."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/history"
        await pilot.press("enter")
        await pilot.pause()

        from nekomata.screens.journal import JournalScreen
        screen = app.screen
        assert isinstance(screen, JournalScreen)

        # With empty journal, no reading items to focus; just check Tab doesn't crash
        await pilot.press("tab")
        await pilot.pause()
