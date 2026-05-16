import pytest

from nekomata.app import NekomataApp
from nekomata.screens.journal import JournalScreen


@pytest.mark.asyncio
async def test_navigate_to_journal():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#journal")
        await pilot.pause()
        assert isinstance(app.screen, JournalScreen)


@pytest.mark.asyncio
async def test_journal_shows_empty_message():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#journal")
        await pilot.pause()
        # No saved readings yet, should show empty message
        assert app.screen.query_one("#reading-list") is not None


@pytest.mark.asyncio
async def test_journal_back():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#journal")
        await pilot.pause()
        assert isinstance(app.screen, JournalScreen)
        await pilot.click("#back")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)
