import pytest

from nekomata.app import NekomataApp


@pytest.mark.asyncio
async def test_app_starts():
    app = NekomataApp()
    async with app.run_test() as pilot:
        assert app.screen is not None


@pytest.mark.asyncio
async def test_home_screen_has_title():
    app = NekomataApp()
    async with app.run_test() as pilot:
        assert app.screen.query_one("#title") is not None


@pytest.mark.asyncio
async def test_home_screen_has_input():
    app = NekomataApp()
    async with app.run_test() as pilot:
        assert app.screen.query_one("#prompt-input") is not None


@pytest.mark.asyncio
async def test_navigate_to_spread_select():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "测试问题"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)


@pytest.mark.asyncio
async def test_spread_select_has_options():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "测试"
        await pilot.press("enter")
        await pilot.pause()
        buttons = app.screen.query("Button")
        ids = [b.id for b in buttons if b.id]
        assert "spread-single" in ids
        assert "spread-past-present-future" in ids


@pytest.mark.asyncio
async def test_reading_screen_shows_cards():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "测试问题"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)


@pytest.mark.asyncio
async def test_reading_screen_card_preview():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "预览测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        assert app.screen.query_one("#card-preview") is not None


@pytest.mark.asyncio
async def test_full_flow_to_interpretation():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "完整流程测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.click("#interpret")
        await pilot.pause()
        from nekomata.screens.interpretation import InterpretationScreen
        assert isinstance(app.screen, InterpretationScreen)
