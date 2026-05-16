import pytest

from nekomata.app import NekomataApp
from nekomata.screens.card_browser import CardBrowserScreen


@pytest.mark.asyncio
async def test_navigate_to_card_browser():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#card-browser")
        await pilot.pause()
        assert isinstance(app.screen, CardBrowserScreen)


@pytest.mark.asyncio
async def test_card_browser_has_filter_buttons():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#card-browser")
        await pilot.pause()
        buttons = app.screen.query("#filter-bar Button")
        ids = [b.id for b in buttons if b.id]
        assert "filter-all" in ids
        assert "filter-major" in ids
        assert "filter-cups" in ids


@pytest.mark.asyncio
async def test_card_browser_shows_cards():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#card-browser")
        await pilot.pause()
        items = app.screen.query("CardListItem")
        assert len(items) > 0


@pytest.mark.asyncio
async def test_card_browser_filter_by_suit():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#card-browser")
        await pilot.pause()
        await pilot.click("#filter-cups")
        await pilot.pause()
        items = app.screen.query("CardListItem")
        assert len(items) == 14


@pytest.mark.asyncio
async def test_card_browser_back():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#card-browser")
        await pilot.pause()
        assert isinstance(app.screen, CardBrowserScreen)
        await pilot.click("#back")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)
